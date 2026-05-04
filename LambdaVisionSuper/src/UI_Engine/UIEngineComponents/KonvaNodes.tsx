import React, { useRef, useEffect, useState } from 'react';
import { Group, Rect, Text, Circle, Transformer, Image as KonvaImage } from 'react-konva';
import { useUIEngine, useDataBinding } from '../UIEngineStores/InspectionStore';
import { useSequencerStore } from '../UIEngineStores/SequencerStores';

const useFrameBgImage = (runtimeSource?: string | Blob | File, defaultSource?: string, isRunning: boolean = false) => {
    const [image, setImage] = useState<HTMLImageElement | undefined>(undefined);

    useEffect(() => {
        // TÌNH HUỐNG MẤT TÍN HIỆU: Đang chạy mà ảnh Runtime rỗng hoặc báo empty
        if (isRunning && (!runtimeSource || runtimeSource === "data:image/empty")) {
            // Màn hình đen chữ đỏ cảnh báo No Signal thay vì lui về Default Image
            const noSignalBase64 = "data:image/svg+xml;charset=UTF-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100%25' height='100%25' viewBox='0 0 100 100'%3E%3Crect width='100%25' height='100%25' fill='%23202124'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' font-size='10' font-family='monospace' fill='%23f28b82' font-weight='bold'%3E⚠️ NO SIGNAL%3C/text%3E%3C/svg%3E";
            const img = new window.Image();
            img.src = noSignalBase64;
            img.onload = () => setImage(img);
            return; 
        }

        // TÌNH HUỐNG BÌNH THƯỜNG / THIẾT KẾ: Ưu tiên Runtime, Fallback về Default
        const activeSource = runtimeSource || defaultSource;
        
        if (!activeSource || activeSource === "data:image/empty") { 
            setImage(undefined); 
            return; 
        }

        const img = new window.Image();
        let objectUrl: string | null = null;

        // BẮT LỖI LOAD ẢNH
        img.onload = () => setImage(img);
        img.onerror = () => {
            console.error("🚨 Lỗi: Konva không thể load ảnh từ nguồn này!");
            setImage(undefined);
        };

        if ((activeSource as any) instanceof Blob || (activeSource as any) instanceof File) {
            objectUrl = URL.createObjectURL((activeSource as any));
            img.src = objectUrl;
        } else if (typeof activeSource === 'string') {
            if (activeSource.startsWith('http')) {
                img.crossOrigin = "Anonymous";
            }
            img.src = activeSource;
        }

        return () => {
            if (objectUrl) URL.revokeObjectURL(objectUrl);
        };
    }, [runtimeSource, defaultSource, isRunning]); 

    return image;
};

export const SceneNodeRenderer = ({ id }: { id: string }) => {
    const node = useUIEngine(state => state.components_map[id]);
    const { nameLabelConfig, selectedNodeIds, updateComponentProps, selectComponents, openActionMenu } = useUIEngine();
    
    if (!node || !node.isVisible) return null;

    const x = useDataBinding(node.bindings, 'x', node.x);
    const y = useDataBinding(node.bindings, 'y', node.y);
    const width = useDataBinding(node.bindings, 'size_x', node.size_x);
    const height = useDataBinding(node.bindings, 'size_y', node.size_y);
    const radius = useDataBinding(node.bindings, 'radius', node.radius);
    const textContent = useDataBinding(node.bindings, 'content', node.content);
    
    const strokeColor = useDataBinding(node.bindings, 'style.strokeColor', node.style?.strokeColor);
    const fillColor = useDataBinding(node.bindings, 'style.fillColor', node.style?.fillColor);
    const fontColor = useDataBinding(node.bindings, 'style.fontColor', node.style?.fontColor);
    const borderThickness = useDataBinding(node.bindings, 'style.border_thickness', node.style?.border_thickness);

    // Lấy dữ liệu Runtime
    const rawBgImage = useDataBinding(node.bindings, 'style.bgImage', node.style?.bgImage);
    // Lấy dữ liệu Default
    const rawDefaultImage = useDataBinding(node.bindings, 'style.default_image', node.style?.default_image);

    // THUẬT TOÁN ƯU TIÊN (ĐÚNG NHƯ BẠN THIẾT KẾ):
    // Nếu Runtime có dữ liệu hợp lệ (không null, không rỗng), dùng Runtime. 
    // Nếu không, Fallback về Default Image.
    const activeSource = (rawBgImage && rawBgImage !== "") ? rawBgImage : rawDefaultImage;

    const bgImage = useFrameBgImage(activeSource);

    const isEngineRunning = useSequencerStore(state => state.isEngineRunning);

    const isSelected = !isEngineRunning && selectedNodeIds.includes(id); 
    const shapeRef = useRef<any>(null);
    const trRef = useRef<any>(null);

    useEffect(() => {
        if (isSelected && trRef.current && shapeRef.current) {
            trRef.current.nodes([shapeRef.current]);
            trRef.current.getLayer().batchDraw();
        }
    }, [isSelected]);

    const handleContextMenu = (e: any) => {
        if (isEngineRunning) return;
        e.evt.preventDefault();
        e.cancelBubble = true;
        const pos = e.target.getStage().getRelativePointerPosition();
        openActionMenu(id, node.type, e.evt.clientX, e.evt.clientY, pos.x, pos.y);
    };

    const handleDragEnd = (e: any) => {
        if (isEngineRunning) return; 
        if (e.target === shapeRef.current) { updateComponentProps(id, { x: e.target.x(), y: e.target.y() }); }
    };

    const commonProps = {
        ref: shapeRef, x, y, rotation: node.rotation, 
        draggable: !isEngineRunning, 
        onClick: (e: any) => { 
            if (isEngineRunning) return; 
            e.cancelBubble = true; 
            selectComponents([id]); 
        },
        onContextMenu: handleContextMenu,
        onDragEnd: handleDragEnd,
    };

    const NameLabel = () => nameLabelConfig.isVisible && node.type !== 'screen' ? (
        <Text 
            x={node.type === 'bounding_circle' ? x - radius : x} 
            y={(node.type === 'bounding_circle' ? y - radius : y) - (nameLabelConfig.fontSize + 4)} 
            text={node.name} 
            fontSize={nameLabelConfig.fontSize} 
            fontFamily={nameLabelConfig.fontFamily}
            fill={nameLabelConfig.fontColor} 
            fontStyle="bold" 
            listening={false} 
        />
    ) : null;

    let NodeComponent = null;

    if (node.type === 'frame') {
        NodeComponent = (
            <Group {...commonProps}>
                <Rect width={width} height={height} stroke={strokeColor} strokeWidth={borderThickness} fill={fillColor} />
                {bgImage && <KonvaImage image={bgImage} width={width} height={height} opacity={0.6} />}
                {node.children_id.map((childId: string) => <SceneNodeRenderer key={childId} id={childId} />)}
            </Group>
        );
    } 
    else if (node.type === 'bounding_box') {
        NodeComponent = <Rect {...commonProps} width={width} height={height} stroke={strokeColor} strokeWidth={borderThickness} fill={fillColor} />;
    } 
    else if (node.type === 'bounding_circle') {
        NodeComponent = <Circle {...commonProps} radius={radius} stroke={strokeColor} strokeWidth={borderThickness} fill={fillColor} />;
    } 
    else if (node.type === 'text') {
        NodeComponent = <Text {...commonProps} text={textContent} fontSize={node.style?.fontSize} fill={fontColor} width={width} height={height} lineHeight={1.5} />;
    }

    return (
        <React.Fragment>
            {NodeComponent}
            <NameLabel />
            {isSelected && <Transformer ref={trRef} boundBoxFunc={(oldB, newB) => newB.width < 5 || newB.height < 5 ? oldB : newB} 
                onTransformEnd={() => {
                    const n = shapeRef.current;
                    const updates: any = { x: n.x(), y: n.y(), rotation: n.rotation() };
                    if (node.type === 'bounding_circle') {
                        updates.radius = radius * Math.max(n.scaleX(), n.scaleY()); 
                    } else {
                        updates.size_x = width * n.scaleX();
                        updates.size_y = height * n.scaleY();
                    }
                    n.scaleX(1); n.scaleY(1);
                    updateComponentProps(id, updates);
                }}
            />}
        </React.Fragment>
    );
};