import React, { useRef, useEffect, useState } from 'react';
import { Group, Rect, Text, Circle, Transformer, Image as KonvaImage, Line } from 'react-konva';
import { useUIEngine, useDataBinding } from '../UIEngineStores/InspectionStore';
import { useSequencerStore } from '../UIEngineStores/SequencerStores';
import { useTagDb } from '../UIEngineStores/GlobalTagsStore';
import { Html } from 'react-konva-utils';

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
    const isTagActive = useTagDb(state => state.tags[node.targetTag] === true);
    
    const activeColor = isTagActive ? (node.style.activeColor || '#81c995') : (node.style.fillColor || '#3c4043');

    const handleInteractionStart = (e: any) => {
        if (!isEngineRunning) return;
        e.cancelBubble = true; 
        if (!node.targetTag) return;
        
        if (node.actionType === 'pulse') writeTag(node.targetTag, true);
        else if (node.actionType === 'setToTrue') writeTag(node.targetTag, true);
        else if (node.actionType === 'setToFalse') writeTag(node.targetTag, false);
        else if (node.actionType === 'toggle') writeTag(node.targetTag, !readTag(node.targetTag));
    };

    const handleInteractionEnd = (e: any) => {
        if (!isEngineRunning) return;
        e.cancelBubble = true;
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
    // 1. SỬA LỖI ĐỌC DATA: 
    // Kiểm tra xem node.data đang là String (Tên Tag) hay là Array (Mảng mẫu mặc định)
    // Nếu là tên Tag, gọi thẳng vào hook useTagDb để lấy mảng dữ liệu thật.
    const tagData = useTagDb(state => typeof node.data === 'string' ? state.tags[node.data] : undefined);
    
    // Nếu tagData có dữ liệu thì dùng, nếu không thì dùng node.data (mảng mẫu)
    const bboxesArray = tagData || node.data;
    const safeArray = Array.isArray(bboxesArray) ? bboxesArray : [];

    // 2. TẤM NỀN ẢO (VIEWPORT) CHỐNG SỤP ĐỔ
    const vpWidth = node.size_x || 100;
    const vpHeight = node.size_y || 100;

    return (
        <Group ref={shapeRef} {...commonProps}>
            
            {/* TẤM NỀN: Hứng trọn sự kiện click/drag, ngăn Transformer tính toán sai */}
            <Rect
                width={vpWidth}
                height={vpHeight}
                fill={!isEngineRunning ? "rgba(138, 180, 248, 0.05)" : "transparent"} 
                stroke={!isEngineRunning ? "#5f6368" : "transparent"} 
                strokeWidth={1}
                dash={[4, 4]}
            />

            {/* NHÃN HIỂN THỊ KHI ĐANG EDIT */}
            {!isEngineRunning && (
                <Text
                    x={4} y={4}
                    text={`[BBox Area: ${safeArray.length} items]`}
                    fill="#5f6368" fontSize={10} fontStyle="italic" listening={false}
                />
            )}

            {/* 3. VẼ CÁC BOUNDING BOX TỪ DỮ LIỆU */}
            {safeArray.map((box: any, idx: number) => {
                // Ép kiểu sang Number để tránh lỗi khi JSON lỡ lưu String
                const bx = Number(box.x) || 0;
                const by = Number(box.y) || 0;
                const bw = Number(box.w) || 0;
                const bh = Number(box.h) || 0;

                return (
                    <Group key={box.id || idx} x={bx} y={by} listening={false}> 
                        <Rect
                            width={bw} height={bh}
                            stroke={box.color || '#ff0000'}
                            strokeWidth={2}
                            dash={!isEngineRunning ? [5, 5] : undefined}
                        />
                        {box.label && (
                            <Text
                                text={box.label} y={-14} fill={box.color || '#ff0000'}
                                fontSize={!isEngineRunning ? 11 : 14} 
                                fontStyle="bold" shadowColor="black"
                                shadowBlur={2} shadowOffsetX={1} shadowOffsetY={1}
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

    const commonProps = {
        x, y, width, height, rotation: node.rotation, draggable: !isEngineRunning, 
        onClick: (e: any) => { if (isEngineRunning) return; e.cancelBubble = true; selectComponents([id]); },
        onContextMenu: (e: any) => {
            if (isEngineRunning) return;
            e.evt.preventDefault(); e.cancelBubble = true;
            const pos = e.target.getStage().getRelativePointerPosition();
            openActionMenu(id, node.type, e.evt.clientX, e.evt.clientY, pos.x, pos.y);
        },
        onDragEnd: (e: any) => { if (!isEngineRunning && e.target === shapeRef.current) updateComponentProps(id, { x: e.target.x(), y: e.target.y() }); }
    };

    let InnerShape = null;
    if (node.type === 'frame') {
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
        InnerShape = <Rect ref={shapeRef} {...commonProps} stroke={strokeColor} strokeWidth={borderThickness} fill={fillColor} />;
    } 
    else if (node.type === 'bounding_circle') {
        const radius = useDataBinding(node.bindings, 'radius', node.radius);
        InnerShape = <Circle ref={shapeRef} {...commonProps} radius={radius} stroke={strokeColor} strokeWidth={borderThickness} fill={fillColor} />;
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