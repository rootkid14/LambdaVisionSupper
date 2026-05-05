import React, { useRef, useEffect, useState } from 'react';
import { Group, Rect, Text, Circle, Transformer, Image as KonvaImage } from 'react-konva';
import { useUIEngine, useDataBinding } from '../UIEngineStores/InspectionStore';
import { useSequencerStore } from '../UIEngineStores/SequencerStores';
import { useTagDb } from '../UIEngineStores/GlobalTagsStore';

// ---------------------------------------------------------
// 1. HOOKS DÙNG CHUNG
// ---------------------------------------------------------
const useFrameBgImage = (runtimeSource?: string | Blob | File, defaultSource?: string, isRunning: boolean = false) => {
    // ... (Giữ nguyên toàn bộ logic useFrameBgImage cũ của bạn[cite: 2])
    const [image, setImage] = useState<HTMLImageElement | undefined>(undefined);
    useEffect(() => {
        if (isRunning && (!runtimeSource || runtimeSource === "data:image/empty")) {
            const noSignalBase64 = "data:image/svg+xml;charset=UTF-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100%25' height='100%25' viewBox='0 0 100 100'%3E%3Crect width='100%25' height='100%25' fill='%23202124'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' font-size='10' font-family='monospace' fill='%23f28b82' font-weight='bold'%3E⚠️ NO SIGNAL%3C/text%3E%3C/svg%3E";
            const img = new window.Image();
            img.src = noSignalBase64;
            img.onload = () => setImage(img);
            return; 
        }
        const activeSource = runtimeSource || defaultSource;
        if (!activeSource || activeSource === "data:image/empty") { setImage(undefined); return; }
        const img = new window.Image();
        let objectUrl: string | null = null;
        img.onload = () => setImage(img);
        img.onerror = () => setImage(undefined);
        if ((activeSource as any) instanceof Blob || (activeSource as any) instanceof File) {
            objectUrl = URL.createObjectURL((activeSource as any));
            img.src = objectUrl;
        } else if (typeof activeSource === 'string') {
            if (activeSource.startsWith('http')) img.crossOrigin = "Anonymous";
            img.src = activeSource;
        }
        return () => { if (objectUrl) URL.revokeObjectURL(objectUrl); };
    }, [runtimeSource, defaultSource, isRunning]); 
    return image;
};

// ---------------------------------------------------------
// 2. DISPATCHER: NGƯỜI ĐIỀU PHỐI CHÍNH (Đã được Refactor)
// ---------------------------------------------------------
export const SceneNodeRenderer = ({ id }: { id: string }) => {
    const node = useUIEngine(state => state.components_map[id]);
    const isVisibleBound = useDataBinding(node?.bindings || [], 'isVisible', node?.isVisible ?? true);

    // Ngăn chặn render nếu node không tồn tại hoặc bị ẩn
    if (!node || !isVisibleBound) return null;

    // PHÂN LUỒNG: Giao việc cho đúng thợ chuyên môn
    switch (node.type) {
        case 'frame':
        case 'bounding_box':
        case 'bounding_circle':
        case 'text':
        case 'soft_button':
            // Các node này xài chung logic Transformer (viền chọn) nên ta gom vào StandardNodeWrapper
            return <StandardNodeWrapper id={id} node={node} />;
        default:
            return null;
    }
};

// ---------------------------------------------------------
// THỢ CHUYÊN MÔN: SOFT BUTTON INNER
// ---------------------------------------------------------
const SoftButtonInner = ({ node, commonProps, isEngineRunning, shapeRef }: any) => {
    const writeTag = useTagDb(state => state.writeTag);
    const readTag = useTagDb(state => state.readTag);
    const isTagActive = useTagDb(state => state.tags[node.targetTag] === true);
    
    // Tự động dùng activeColor khi được nhấn
    const activeColor = isTagActive ? (node.style.activeColor || '#81c995') : (node.style.fillColor || '#3c4043');

    const handleInteractionStart = (e: any) => {
        if (!isEngineRunning) return;
        e.cancelBubble = true; // QUAN TRỌNG: Chặn click lan ra màn hình gây lỗi
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
            ref={shapeRef} // <--- GẮN REF TRỰC TIẾP VÀO ĐÂY ĐỂ HIỆN TRANSFORMER RESIZE
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

// ---------------------------------------------------------
// WRAPPER CHUNG
// ---------------------------------------------------------
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

    // BỎ 'ref' RA KHỎI COMMON PROPS (Sẽ gắn thủ công vào từng thẻ)
    // THÊM width, height VÀO ĐỂ TRANSFORMER BAO QUANH ĐƯỢC GROUP
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
        const bgImage = useFrameBgImage((rawBgImage && rawBgImage !== "") ? rawBgImage : rawDefaultImage, undefined, isEngineRunning);
        
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
    // TRUYỀN THÊM SHAPEREF XUỐNG CHO NÚT ẤN
    else if (node.type === 'soft_button') {
        InnerShape = <SoftButtonInner node={node} commonProps={commonProps} isEngineRunning={isEngineRunning} shapeRef={shapeRef} />;
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