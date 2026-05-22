import React, { useRef, useEffect, useState } from 'react';
import { Group, Rect, Text, Circle, Transformer, Image as KonvaImage, Line } from 'react-konva';
import { useUIEngine, useDataBinding } from '../UIEngineStores/InspectionStore';
import { useSequencerStore } from '../UIEngineStores/SequencerStores';
import { useTagDb } from '../UIEngineStores/GlobalTagsStore';
import { Html } from 'react-konva-utils';
import { SequencerEngine } from '../UIEngineStores/SequencerEngine';

const useFrameBgImage = (runtimeSource?: string | Blob | File, defaultSource?: string) => {
    const [image, setImage] = useState<HTMLImageElement | undefined>(undefined);
    
    useEffect(() => {
        // Ưu tiên dùng ảnh runtime, nếu không có thì xài ảnh mặc định
        const activeSource = runtimeSource || defaultSource;
        
        // NẾU KHÔNG CÓ ẢNH: Xóa ảnh hiện tại đi (để lộ lớp Fill Color phía dưới)
        if (!activeSource || activeSource === "data:image/empty") { 
            setImage(undefined); 
            return; 
        }
        
        const img = new window.Image();
        let objectUrl: string | null = null;
        
        img.onload = () => setImage(img);
        img.onerror = () => setImage(undefined); // Nếu link ảnh lỗi, cũng ẩn đi để hiện Fill Color
        
        if (activeSource instanceof Blob || (activeSource as any) instanceof File) {
            objectUrl = URL.createObjectURL((activeSource as any));
            img.src = objectUrl;
        } else if (typeof activeSource === 'string') {
            if (activeSource.startsWith('http')) img.crossOrigin = "Anonymous";
            img.src = activeSource;
        }
        
        return () => { if (objectUrl) URL.revokeObjectURL(objectUrl); };
    }, [runtimeSource, defaultSource]); 
    
    return image;
};

export const SceneNodeRenderer = ({ id }: { id: string }) => {
    const node = useUIEngine(state => state.components_map[id]);
    const isVisibleBound = useDataBinding(node?.bindings || [], 'isVisible', node?.isVisible ?? true);

    if (!node || !isVisibleBound) return null;
    return <StandardNodeWrapper id={id} node={node} />;
};

const SoftButtonInner = ({ node, commonProps, isEngineRunning, shapeRef }: any) => {
    const writeTag = useTagDb(state => state.writeTag);
    const readTag = useTagDb(state => state.readTag);
    
    // Nếu nút không có targetTag (như trường hợp chạy Script độc lập) thì isTagActive sẽ là false
    const isTagActive = useTagDb(state => node.targetTag ? state.tags[node.targetTag] === true : false);
    
    const activeColor = isTagActive ? (node.style.activeColor || '#81c995') : (node.style.fillColor || '#3c4043');

    // 1. CHUYỂN HÀM THÀNH BẤT ĐỒNG BỘ (ASYNC) ĐỂ CHỜ SCRIPT CHẠY
    const handleInteractionStart = async (e: any) => {
        if (!isEngineRunning) return;
        e.cancelBubble = true; 

        // ==========================================
        // KHỐI LOGIC MỚI: THỰC THI SCRIPT (SOFT BUTTON)
        // ==========================================
        if (node.actionType === 'script' && node.script_content) {
            try {
                const tagStore = useTagDb.getState();
                const uiStore = useUIEngine.getState();
                
                // 1. ÁNH XẠ BIẾN IN TỪ ALIAS
                const IN: any = {};
                const inputAliases = node.input_aliases || {};
                for (const [alias, tagId] of Object.entries(inputAliases)) {
                    IN[alias] = tagStore.readTag(tagId as string);
                }

                // 2. KHỞI TẠO BIẾN OUT
                const OUT: Record<string, any> = {}; 
                
                // 3. ĐỐI TƯỢNG UI HELPER
                const UI = {
                    get: (query: string) => {
                        const uiMap = uiStore.components_map;
                        let comp = uiMap[query];
                        if (!comp) comp = Object.values(uiMap).find((c: any) => c.name === query);
                        if (!comp) return null;
                        
                        return {
                            id: comp.id, name: comp.name, type: comp.type,
                            x: comp.x, y: comp.y, w: comp.size_x, h: comp.size_y,
                            isVisible: comp.isVisible, style: { ...comp.style }
                        };
                    },
                    set: (query: string, props: any) => {
                        const uiMap = uiStore.components_map;
                        let comp = uiMap[query];
                        if (!comp) comp = Object.values(uiMap).find((c: any) => c.name === query);
                        if (!comp) return false;
                        
                        const updatePayload: any = { ...props };
                        if (updatePayload.w !== undefined) { updatePayload.size_x = updatePayload.w; delete updatePayload.w; }
                        if (updatePayload.h !== undefined) { updatePayload.size_y = updatePayload.h; delete updatePayload.h; }
                        if (updatePayload.style) updatePayload.style = { ...(comp.style || {}), ...updatePayload.style };
                        
                        uiStore.updateComponentProps(comp.id, updatePayload);
                        return true;
                    }
                };

                // 4. ĐỐI TƯỢNG "ENGINE" (Phiên bản dành cho Nút Bấm - Không có Token cục bộ)
                const seqEngine = SequencerEngine.getInstance();
                const ENGINE = {
                    log: (msg: any) => {
                        const strMsg = typeof msg === 'object' ? JSON.stringify(msg) : String(msg);
                        useSequencerStore.getState().appendCompilerLog(`[UI Button: ${node.content || 'Script'}] ${strMsg}`);
                    },
                    
                    spawnAt: (nodeName: string) => {
                        const uuid = seqEngine.getUuidByIdentity(nodeName);
                        if (uuid) return seqEngine.spawnToken(uuid);
                        console.error(`Không tìm thấy Node có tên: ${nodeName}`);
                    },

                    // 2. Di chuyển toàn bộ Token từ Node A sang Node B
                    moveAll: (fromNodeName: string, toNodeName: string) => {
                        const fromUuid = seqEngine.getUuidByIdentity(fromNodeName);
                        const toUuid = seqEngine.getUuidByIdentity(toNodeName);
                        if (fromUuid && toUuid) {
                            const tokensAtNode = Object.entries(seqEngine.token_list)
                                .filter(([_, t]) => t.node_uuid === fromUuid)
                                .map(([id, _]) => id);
                            
                            tokensAtNode.forEach(id => seqEngine.hijackToken(id, toUuid));
                            return tokensAtNode.length;
                        }
                    },

                    // 3. Tiêu diệt toàn bộ Token đang đứng tại một Node cụ thể
                    killAt: (nodeName: string) => {
                        const uuid = seqEngine.getUuidByIdentity(nodeName);
                        if (uuid) {
                            let count = 0;
                            for (const id in seqEngine.token_list) {
                                if (seqEngine.token_list[id].node_uuid === uuid) {
                                    seqEngine.killToken(id);
                                    count++;
                                }
                            }
                            return count;
                        }
                    },

                    // 4. Lấy danh sách ID của các Token đang đứng tại Node này (để xử lý nâng cao)
                    getTokensAt: (nodeName: string) => {
                        const uuid = seqEngine.getUuidByIdentity(nodeName);
                        return uuid ? Object.entries(seqEngine.token_list)
                            .filter(([_, t]) => t.node_uuid === uuid)
                            .map(([id, _]) => id) : [];
                    },
                    // Cấp quyền đẻ Token mới để UI có thể kích hoạt 1 luồng Logic
                    spawn: (targetNodeId: string) => seqEngine.spawnToken(targetNodeId),

                    // Quyền năng Query & Điều phối diện rộng
                    queryByLabel: (label: string) => seqEngine.getTokensByLabel(label),
                    queryByHistory: (node_uuid: string) => seqEngine.getTokensByHistory(node_uuid),
                    
                    kill: (id: string) => seqEngine.killToken(id),
                    killAllByLabel: (label: string) => seqEngine.killTokensByLabel(label),
                    hijack: (id: string, targetNodeId: string) => seqEngine.hijackToken(id, targetNodeId)
                };

                // 5. THỰC THI JIT COMPILER
                const AsyncFunction = Object.getPrototypeOf(async function(){}).constructor as any;
                const userScript = new AsyncFunction('IN', 'OUT', 'UI', 'ENGINE', node.script_content);
                await userScript(IN, OUT, UI, ENGINE);
                
                // 6. ĐẨY BIẾN OUT RA GLOBAL TAGS (Theo Alias)
                const outputAliases = node.output_aliases || {};
                for (const [alias, tagId] of Object.entries(outputAliases)) {
                    if (OUT[alias] !== undefined) {
                        tagStore.writeTag(tagId as string, OUT[alias]);
                    }
                }

            } catch (error) {
                console.error(`[Soft Button: ${node.name}] Script Execution Error:`, error);
            }
            return; // Quan trọng: Return ngay để không chạy xuống khối logic cũ bên dưới
        }

        // ==========================================
        // KHỐI LOGIC CŨ (Dành cho các Action: Toggle, Pulse...)
        // ==========================================
        if (!node.targetTag) return;
        
        if (node.actionType === 'pulse') writeTag(node.targetTag, true);
        else if (node.actionType === 'setToTrue') writeTag(node.targetTag, true);
        else if (node.actionType === 'setToFalse') writeTag(node.targetTag, false);
        else if (node.actionType === 'toggle') writeTag(node.targetTag, !readTag(node.targetTag));
    };

    const handleInteractionEnd = (e: any) => {
        if (!isEngineRunning) return;
        e.cancelBubble = true;
        // Pulse nhả chuột ra thì tắt
        if (node.targetTag && node.actionType === 'pulse') writeTag(node.targetTag, false);
    };

    return (
        <Group
            ref={shapeRef}
            {...commonProps}
            onMouseDown={handleInteractionStart} 
            onTouchStart={handleInteractionStart}
            onMouseUp={handleInteractionEnd} 
            onTouchEnd={handleInteractionEnd}
            onMouseEnter={(e) => { if (isEngineRunning) { const c = e.target.getStage()?.container(); if (c) c.style.cursor = 'pointer'; } }}
            onMouseLeave={(e) => { const c = e.target.getStage()?.container(); if (c) c.style.cursor = 'default'; }}
        >
            <Rect
                width={node.size_x} height={node.size_y}
                fill={activeColor} cornerRadius={node.style.cornerRadius || 4}
                stroke={isTagActive ? '#ffffff' : '#3c4043'} strokeWidth={isTagActive ? 2 : 1}
                shadowBlur={isTagActive ? 10 : 2} shadowColor={node.style.activeColor || '#81c995'} shadowOpacity={0.5}
            />
            <Text
                width={node.size_x} height={node.size_y}
                text={node.content} fill={node.style.fontColor || 'white'}
                fontSize={node.style.fontSize || 14} fontStyle="bold"
                align="center" verticalAlign="middle" listening={false}
            />
        </Group>
    );
};

const TextInputInner = ({ node, commonProps, isEngineRunning, shapeRef }: any) => {
    const writeTag = useTagDb(state => state.writeTag);
    const val = useTagDb(state => state.tags[node.targetTag] as string) || '';

    return (
        <Group ref={shapeRef} {...commonProps}>
            {!isEngineRunning ? (
                <>
                    <Rect width={node.size_x} height={node.size_y} fill="#171717" stroke={node.style.strokeColor || "#3c4043"} strokeWidth={1} cornerRadius={4} />
                    <Text x={8} y={node.size_y / 2 - 6} text={`[Input: ${node.targetTag || 'No Tag'}]`} fill="#5f6368" fontSize={12} fontStyle="italic" listening={false} />
                </>
            ) : (
                <Html transform={true}>
                    <input 
                        type="text"
                        value={val}
                        onChange={(e) => writeTag(node.targetTag, e.target.value)}
                        style={{
                            width: `${node.size_x}px`,
                            height: `${node.size_y}px`,
                            backgroundColor: '#171717',
                            color: node.style.fontColor || '#e8eaed',
                            border: `1px solid ${node.style.strokeColor || '#8ab4f8'}`,
                            borderRadius: '4px',
                            padding: '0 8px',
                            fontSize: `${node.style.fontSize || 14}px`,
                            outline: 'none',
                            pointerEvents: 'auto'
                        }}
                        onPointerDown={(e) => e.stopPropagation()} 
                    />
                </Html>
            )}
        </Group>
    );
};

const ComboboxInner = ({ node, commonProps, isEngineRunning, shapeRef }: any) => {
    const writeTag = useTagDb(state => state.writeTag);
    const rawOptions = useTagDb(state => state.tags[node.sourceTag]);
    const options = Array.isArray(rawOptions) ? rawOptions : [];
    const selectedVal = useTagDb(state => state.tags[node.targetTag] as string) || '';

    return (
        <Group ref={shapeRef} {...commonProps}>
            {!isEngineRunning ? (
                <>
                    <Rect width={node.size_x} height={node.size_y} fill="#171717" stroke={node.style.strokeColor || "#3c4043"} strokeWidth={1} cornerRadius={4} />
                    <Text x={8} y={node.size_y / 2 - 6} text={`Dropdown [${options.length} items]`} fill="#5f6368" fontSize={12} fontStyle="italic" listening={false} />
                    <Line points={[node.size_x - 20, node.size_y / 2 - 2, node.size_x - 10, node.size_y / 2 - 2, node.size_x - 15, node.size_y / 2 + 4]} fill="#5f6368" closed listening={false}/>
                </>
            ) : (
                <Html transform={true}>
                    <select 
                        value={selectedVal}
                        onChange={(e) => writeTag(node.targetTag, e.target.value)}
                        style={{
                            width: `${node.size_x}px`,
                            height: `${node.size_y}px`,
                            backgroundColor: '#171717',
                            color: node.style.fontColor || '#e8eaed',
                            border: `1px solid ${node.style.strokeColor || '#8ab4f8'}`,
                            borderRadius: '4px',
                            padding: '0 8px',
                            fontSize: `${node.style.fontSize || 14}px`,
                            outline: 'none',
                            cursor: 'pointer',
                            pointerEvents: 'auto'
                        }}
                        onPointerDown={(e) => e.stopPropagation()}
                    >
                        <option value="" disabled>-- Chọn --</option>
                        {options.map((opt, idx) => (
                            <option key={idx} value={String(opt)}>{String(opt)}</option>
                        ))}
                    </select>
                </Html>
            )}
        </Group>
    );
};

const SliderInner = ({ node, commonProps, isEngineRunning, shapeRef }: any) => {
    const writeTag = useTagDb(state => state.writeTag);
    const val = useTagDb(state => state.tags[node.targetTag] as number) || 0;
    
    const min = node.min || 0;
    const max = node.max || 100;
    const trackWidth = node.size_x;
    const handleRadius = node.size_y / 2;

    const clampedVal = Math.max(min, Math.min(max, val));
    const handleX = ((clampedVal - min) / (max - min)) * trackWidth;

    const handleDragMove = (e: any) => {
        if (!isEngineRunning || !node.targetTag) return;
        const pointerPos = e.target.getStage().getRelativePointerPosition();
        
        let newLocalX = pointerPos.x - commonProps.x;
        newLocalX = Math.max(0, Math.min(trackWidth, newLocalX));
        
        const newValue = (newLocalX / trackWidth) * (max - min) + min;
        writeTag(node.targetTag, parseFloat(newValue.toFixed(2))); 
    };

    return (
        <Group ref={shapeRef} {...commonProps}>
            <Rect x={0} y={handleRadius - 2} width={trackWidth} height={4} fill="#3c4043" cornerRadius={2} />
            <Rect x={0} y={handleRadius - 2} width={handleX} height={4} fill={node.style.activeColor || "#8ab4f8"} cornerRadius={2} />
            
            <Circle 
                x={handleX} 
                y={handleRadius} 
                radius={handleRadius} 
                fill={node.style.fillColor || "#ffffff"} 
                shadowBlur={4} shadowColor="black" shadowOpacity={0.5}
                draggable={isEngineRunning}
                dragBoundFunc={function(this: any, pos: any) {
                    return { x: Math.max(this.getAbsolutePosition().x - handleX, Math.min(this.getAbsolutePosition().x + (trackWidth - handleX), pos.x)), y: this.getAbsolutePosition().y };
                }}
                onDragMove={handleDragMove}
                onMouseEnter={(e) => { if (isEngineRunning) { const c = e.target.getStage()?.container(); if(c) c.style.cursor = 'grab'; } }}
                onMouseLeave={(e) => { const c = e.target.getStage()?.container(); if(c) c.style.cursor = 'default'; }}
            />
        </Group>
    );
};

const CheckboxInner = ({ node, commonProps, isEngineRunning, shapeRef }: any) => {
    const writeTag = useTagDb(state => state.writeTag);
    const isChecked = useTagDb(state => state.tags[node.targetTag] as boolean) || false;

    const handleToggle = (e: any) => {
        if (!isEngineRunning) return;
        e.cancelBubble = true;
        if (node.targetTag) writeTag(node.targetTag, !isChecked);
    };

    const boxSize = Math.min(node.size_x, node.size_y);

    return (
        <Group 
            ref={shapeRef} {...commonProps} 
            onMouseDown={handleToggle} onTouchStart={handleToggle}
            onMouseEnter={(e) => { if (isEngineRunning) { const c = e.target.getStage()?.container(); if(c) c.style.cursor = 'pointer'; } }}
            onMouseLeave={(e) => { const c = e.target.getStage()?.container(); if(c) c.style.cursor = 'default'; }}
        >
            <Rect 
                width={boxSize} height={boxSize} 
                fill={isChecked ? (node.style.activeColor || '#8ab4f8') : '#171717'} 
                stroke={node.style.strokeColor || '#3c4043'} 
                strokeWidth={2} cornerRadius={4} 
            />
            {isChecked && (
                <Line 
                    points={[boxSize * 0.2, boxSize * 0.5, boxSize * 0.4, boxSize * 0.7, boxSize * 0.8, boxSize * 0.3]} 
                    stroke="#202124" strokeWidth={3} lineCap="round" lineJoin="round" listening={false} 
                />
            )}
            <Text 
                x={boxSize + 10} y={boxSize / 2 - 7} 
                text={node.content} fill={node.style.fontColor || '#e8eaed'} 
                fontSize={node.style.fontSize || 14} listening={false} 
            />
        </Group>
    );
};

const DynamicBBoxGroup = ({ node, commonProps, isEngineRunning, shapeRef }: any) => {
    const writeTag = useTagDb(state => state.writeTag);
    // Kiểm tra xem data đang liên kết với biến Tag nào
    const isBoundToTag = typeof node.data === 'string';
    const tagData = useTagDb(state => isBoundToTag ? state.tags[node.data] : undefined);
    
    const bboxesArray = tagData || node.data;
    const safeArray = Array.isArray(bboxesArray) ? bboxesArray : [];
    const vpWidth = node.size_x || 100;
    const vpHeight = node.size_y || 100;

    // LƯU LẠI VỊ TRÍ MỚI KHI KÉO THẢ BOX
    const handleBoxDragEnd = (e: any, idx: number) => {
        if (!isEngineRunning || !isBoundToTag) return;
        e.cancelBubble = true;
        
        const newX = parseFloat(e.target.x().toFixed(2));
        const newY = parseFloat(e.target.y().toFixed(2));
        
        const newArray = [...safeArray];
        newArray[idx] = { ...newArray[idx], x: newX, y: newY };
        writeTag(node.data, newArray);
    };

    return (
        <Group ref={shapeRef} {...commonProps}>
            <Rect width={vpWidth} height={vpHeight} fill={!isEngineRunning ? "rgba(138, 180, 248, 0.05)" : "transparent"} stroke={!isEngineRunning ? "#5f6368" : "transparent"} strokeWidth={1} dash={[4, 4]} />
            {!isEngineRunning && <Text x={4} y={4} text={`[BBox Area: ${safeArray.length} items]`} fill="#5f6368" fontSize={10} fontStyle="italic" listening={false} />}

            {safeArray.map((box: any, idx: number) => {
                const bx = Number(box.x) || 0;
                const by = Number(box.y) || 0;
                const bw = Number(box.w) || 0;
                const bh = Number(box.h) || 0;

                return (
                    <Group 
                        key={box.id || idx} 
                        x={bx} y={by} 
                        draggable={isEngineRunning && isBoundToTag} // CHỈ ĐƯỢC KÉO KHI ĐANG CHẠY & CÓ BINDING
                        onDragEnd={(e) => handleBoxDragEnd(e, idx)}
                        onMouseEnter={(e) => { if (isEngineRunning && isBoundToTag) { const c = e.target.getStage()?.container(); if(c) c.style.cursor = 'move'; } }}
                        onMouseLeave={(e) => { if (isEngineRunning && isBoundToTag) { const c = e.target.getStage()?.container(); if(c) c.style.cursor = 'default'; } }}
                    > 
                        <Rect name="bbox-rect" width={bw} height={bh} stroke={box.color || '#ff0000'} strokeWidth={2} dash={!isEngineRunning ? [5, 5] : undefined} />
                        {box.label && <Text text={box.label} y={-14} fill={box.color || '#ff0000'} fontSize={!isEngineRunning ? 11 : 14} fontStyle="bold" shadowColor="black" shadowBlur={2} shadowOffsetX={1} shadowOffsetY={1} />}
                        
                        {/* TÍNH NĂNG MỚI: NÚM KÉO RESIZE */}
                        {isEngineRunning && isBoundToTag && (
                            <Rect 
                                x={bw - 6} y={bh - 6} width={12} height={12} 
                                fill={box.color || '#ff0000'}
                                draggable
                                onDragMove={(e) => {
                                    e.cancelBubble = true;
                                    // Bóp méo giao diện (UI) ngay lập tức để đạt 60FPS
                                    const newW = Math.max(10, e.target.x() + 6);
                                    const newH = Math.max(10, e.target.y() + 6);
                                    const rect = (e.target as any).getParent().findOne('.bbox-rect');
                                    if (rect) { rect.width(newW); rect.height(newH); }
                                }}
                                onDragEnd={(e) => {
                                    e.cancelBubble = true;
                                    // Khi thả chuột ra thì mới tiến hành ghi đè vào Tag Database
                                    const newW = parseFloat(Math.max(10, e.target.x() + 6).toFixed(2));
                                    const newH = parseFloat(Math.max(10, e.target.y() + 6).toFixed(2));
                                    const newArray = [...safeArray];
                                    newArray[idx] = { ...newArray[idx], w: newW, h: newH };
                                    writeTag(node.data, newArray);
                                }}
                                onMouseEnter={(e) => { const c = e.target.getStage()?.container(); if(c) c.style.cursor = 'nwse-resize'; e.cancelBubble = true; }}
                                onMouseLeave={(e) => { const c = e.target.getStage()?.container(); if(c) c.style.cursor = 'move'; e.cancelBubble = true; }}
                            />
                        )}
                    </Group>
                );
            })}
        </Group>
    );
};

const StandardNodeWrapper = ({ id, node }: { id: string, node: any }) => {
    const { nameLabelConfig, selectedNodeIds, updateComponentProps, selectComponents, openActionMenu } = useUIEngine();
    const isEngineRunning = useSequencerStore(state => state.isEngineRunning);
    const isSelected = !isEngineRunning && selectedNodeIds.includes(id); 
    const writeTag = useTagDb(state => state.writeTag);

    const shapeRef = useRef<any>(null);
    const trRef = useRef<any>(null);

    const x = useDataBinding(node.bindings, 'x', node.x);
    const y = useDataBinding(node.bindings, 'y', node.y);
    const width = useDataBinding(node.bindings, 'size_x', node.size_x);
    const height = useDataBinding(node.bindings, 'size_y', node.size_y);
    const strokeColor = useDataBinding(node.bindings, 'style.strokeColor', node.style?.strokeColor);
    const fillColor = useDataBinding(node.bindings, 'style.fillColor', node.style?.fillColor);
    const borderThickness = useDataBinding(node.bindings, 'style.border_thickness', node.style?.border_thickness);

    useEffect(() => {
        if (isSelected && trRef.current && shapeRef.current) {
            trRef.current.nodes([shapeRef.current]);
            trRef.current.getLayer().batchDraw();
        }
    }, [isSelected]);

    // CẤP QUYỀN KÉO THẢ TRONG LÚC RUNTIME CHO BBOX VÀ CIRCLE
    const isDraggableType = node.type === 'bounding_box' || node.type === 'bounding_circle';
    const canDrag = !isEngineRunning || isDraggableType;

    const commonProps = {
        x, y, width, height, rotation: node.rotation, draggable: canDrag, 
        onClick: (e: any) => { if (isEngineRunning) return; e.cancelBubble = true; selectComponents([id]); },
        onContextMenu: (e: any) => {
            if (isEngineRunning) return;
            e.evt.preventDefault(); e.cancelBubble = true;
            const pos = e.target.getStage().getRelativePointerPosition();
            openActionMenu(id, node.type, e.evt.clientX, e.evt.clientY, pos.x, pos.y);
        },
        onDragEnd: (e: any) => { 
            if (e.target !== shapeRef.current) return;
            const newX = parseFloat(e.target.x().toFixed(2));
            const newY = parseFloat(e.target.y().toFixed(2));

            if (!isEngineRunning) {
                updateComponentProps(id, { x: newX, y: newY });
            } else {
                // ENGINE ĐANG CHẠY: Cập nhật ngược lại vào Global Tag (nếu có bind) hoặc Component
                const xBinding = node.bindings?.find((b: any) => b.prop === 'x');
                const yBinding = node.bindings?.find((b: any) => b.prop === 'y');
                
                if (xBinding) writeTag(xBinding.tag, newX);
                else updateComponentProps(id, { x: newX });

                if (yBinding) writeTag(yBinding.tag, newY);
                else updateComponentProps(id, { y: newY });
            }
        },
        onMouseEnter: (e: any) => { 
             if (isEngineRunning && isDraggableType) { 
                 const c = e.target.getStage()?.container(); 
                 if(c) c.style.cursor = 'move'; 
             } 
        },
        onMouseLeave: (e: any) => { 
             if (isEngineRunning && isDraggableType) { 
                 const c = e.target.getStage()?.container(); 
                 if(c) c.style.cursor = 'default'; 
             } 
        }
    };

    let InnerShape = null;
    if (node.type === 'frame') {
        // ... (Giữ nguyên khối code frame)
        const rawBgImage = useDataBinding(node.bindings, 'style.bgImage', node.style?.bgImage);
        const rawDefaultImage = useDataBinding(node.bindings, 'style.default_image', node.style?.default_image);
        const bgImage = useFrameBgImage((rawBgImage && rawBgImage !== "") ? rawBgImage : rawDefaultImage, undefined);
        
        InnerShape = (
            <Group ref={shapeRef} {...commonProps}>
                <Rect width={width} height={height} stroke={strokeColor} strokeWidth={borderThickness} fill={fillColor} />
                {bgImage && <KonvaImage image={bgImage} width={width} height={height} opacity={0.6} />}
                {node.children_id?.map((childId: string) => <SceneNodeRenderer key={childId} id={childId} />)}
            </Group>
        );
    } 
    else if (node.type === 'bounding_box') {
        InnerShape = (
            <Group ref={shapeRef} {...commonProps}>
                <Rect name="bbox-rect" width={width} height={height} stroke={strokeColor} strokeWidth={borderThickness} fill={fillColor} />
                {isEngineRunning && (
                    <Rect 
                        x={width - 6} y={height - 6} width={12} height={12} 
                        fill={strokeColor || '#ff0000'}
                        draggable
                        onDragMove={(e) => {
                            e.cancelBubble = true;
                            const newW = Math.max(10, e.target.x() + 6);
                            const newH = Math.max(10, e.target.y() + 6);
                            const rect = (e.target as any).getParent().findOne('.bbox-rect');
                            if (rect) { rect.width(newW); rect.height(newH); }
                        }}
                        onDragEnd={(e) => {
                            e.cancelBubble = true;
                            const newW = parseFloat(Math.max(10, e.target.x() + 6).toFixed(2));
                            const newH = parseFloat(Math.max(10, e.target.y() + 6).toFixed(2));
                            
                            const wBinding = node.bindings?.find((b: any) => b.prop === 'size_x');
                            const hBinding = node.bindings?.find((b: any) => b.prop === 'size_y');
                            
                            if (wBinding) writeTag(wBinding.tag, newW);
                            else updateComponentProps(id, { size_x: newW });

                            if (hBinding) writeTag(hBinding.tag, newH);
                            else updateComponentProps(id, { size_y: newH });
                        }}
                        onMouseEnter={(e) => { const c = e.target.getStage()?.container(); if(c) c.style.cursor = 'nwse-resize'; e.cancelBubble = true; }}
                        onMouseLeave={(e) => { const c = e.target.getStage()?.container(); if(c) c.style.cursor = 'move'; e.cancelBubble = true; }}
                    />
                )}
            </Group>
        );
    } 
    else if (node.type === 'bounding_circle') {
        const radius = useDataBinding(node.bindings, 'radius', node.radius);
        InnerShape = (
            <Group ref={shapeRef} {...commonProps}>
                <Circle name="bbox-circle" radius={radius} stroke={strokeColor} strokeWidth={borderThickness} fill={fillColor} />
                {isEngineRunning && (
                    <Rect 
                        x={radius - 6} y={-6} width={12} height={12} 
                        fill={strokeColor || '#ff0000'}
                        draggable
                        onDragMove={(e) => {
                            e.cancelBubble = true;
                            const newR = Math.max(5, e.target.x() + 6);
                            e.target.y(-6); // Khoá cứng trục Y
                            const circle = (e.target as any).getParent().findOne('.bbox-circle');
                            if (circle) circle.radius(newR);
                        }}
                        onDragEnd={(e) => {
                            e.cancelBubble = true;
                            const newR = parseFloat(Math.max(5, e.target.x() + 6).toFixed(2));
                            const rBinding = node.bindings?.find((b: any) => b.prop === 'radius');
                            if (rBinding) writeTag(rBinding.tag, newR);
                            else updateComponentProps(id, { radius: newR });
                        }}
                        onMouseEnter={(e) => { const c = e.target.getStage()?.container(); if(c) c.style.cursor = 'ew-resize'; e.cancelBubble = true; }}
                        onMouseLeave={(e) => { const c = e.target.getStage()?.container(); if(c) c.style.cursor = 'move'; e.cancelBubble = true; }}
                    />
                )}
            </Group>
        );
    }
    else if (node.type === 'text') {
        const textContent = useDataBinding(node.bindings, 'content', node.content);
        const fontColor = useDataBinding(node.bindings, 'style.fontColor', node.style?.fontColor);
        InnerShape = <Text ref={shapeRef} {...commonProps} text={textContent} fontSize={node.style?.fontSize} fill={fontColor} width={width} height={height} lineHeight={1.5} />;
    }
    else if (node.type === 'soft_button') {
        InnerShape = <SoftButtonInner node={node} commonProps={commonProps} isEngineRunning={isEngineRunning} shapeRef={shapeRef} />;
    }
    else if (node.type === 'text_input') {
        InnerShape = <TextInputInner node={node} commonProps={commonProps} isEngineRunning={isEngineRunning} shapeRef={shapeRef} />;
    }
    else if (node.type === 'combobox') {
        InnerShape = <ComboboxInner node={node} commonProps={commonProps} isEngineRunning={isEngineRunning} shapeRef={shapeRef} />;
    }
    else if (node.type === 'slider') {
        InnerShape = <SliderInner node={node} commonProps={commonProps} isEngineRunning={isEngineRunning} shapeRef={shapeRef} />;
    }
    else if (node.type === 'checkbox') {
        InnerShape = <CheckboxInner node={node} commonProps={commonProps} isEngineRunning={isEngineRunning} shapeRef={shapeRef} />;
    }
    else if (node.type === 'dynamic_bboxes') {
        InnerShape = <DynamicBBoxGroup node={node} commonProps={commonProps} isEngineRunning={isEngineRunning} shapeRef={shapeRef} />;
    }

    return (
        <React.Fragment>
            {InnerShape}
            {nameLabelConfig.isVisible && node.type !== 'screen' && (
                <Text 
                    x={node.type === 'bounding_circle' ? x - node.radius : x} 
                    y={(node.type === 'bounding_circle' ? y - node.radius : y) - (nameLabelConfig.fontSize + 4)} 
                    text={node.name} fontSize={nameLabelConfig.fontSize} fontFamily={nameLabelConfig.fontFamily}
                    fill={nameLabelConfig.fontColor} fontStyle="bold" listening={false} 
                />
            )}
            {isSelected && <Transformer ref={trRef} boundBoxFunc={(oldB, newB) => newB.width < 5 || newB.height < 5 ? oldB : newB} 
                onTransformEnd={() => {
                    const n = shapeRef.current;
                    const updates: any = { x: n.x(), y: n.y(), rotation: n.rotation() };
                    if (node.type === 'bounding_circle') updates.radius = node.radius * Math.max(n.scaleX(), n.scaleY()); 
                    else { updates.size_x = width * n.scaleX(); updates.size_y = height * n.scaleY(); }
                    n.scaleX(1); n.scaleY(1);
                    updateComponentProps(id, updates);
                }}
            />}
        </React.Fragment>
    );
};