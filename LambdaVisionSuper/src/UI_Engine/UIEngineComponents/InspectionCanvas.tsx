import React, { useRef, useState, useEffect } from 'react';
import { Stage, Layer, Rect } from 'react-konva';
import { useUIEngine, useDataBinding } from '../UIEngineStores/InspectionStore';
import { SceneNodeRenderer } from './KonvaNodes';
import { useSequencerStore } from '../UIEngineStores/SequencerStores';

export const InspectionCanvas = () => {
    const containerRef = useRef<HTMLDivElement>(null);
    const stageRef = useRef<any>(null);
    
    // Lấy thêm viewportMode và setViewportMode từ Store
    const { activeScreenId, components_map, selectComponents, openActionMenu, closeActionMenu, viewportMode, setViewportMode } = useUIEngine();
    
    const [scale, setScale] = useState(1);
    const [position, setPosition] = useState({ x: 0, y: 0 });

    const screenData = components_map[activeScreenId || ''];
    const screenBgColor = useDataBinding(screenData?.bindings, 'style.fillColor', screenData?.style?.fillColor || '#171717');

    // --- THUẬT TOÁN: FULL VIEWPORT (FIT TO SCREEN) ---
    useEffect(() => {
        if (viewportMode === 'fullViewPort' && screenData && containerRef.current) {
            const fitToViewport = () => {
                const container = containerRef.current;
                if (!container) return;

                const PADDING = 60; // Lề an toàn xung quanh
                const cw = container.clientWidth;
                const ch = container.clientHeight;

                // Tính toán tỷ lệ Zoom tối đa có thể để vừa chiều rộng hoặc chiều cao
                const scaleX = (cw - PADDING) / screenData.size_x;
                const scaleY = (ch - PADDING) / screenData.size_y;
                const newScale = Math.min(scaleX, scaleY);

                // Tính toán tọa độ X, Y để căn chính giữa
                const newX = (cw - (screenData.size_x * newScale)) / 2;
                const newY = (ch - (screenData.size_y * newScale)) / 2;

                setScale(newScale);
                setPosition({ x: newX, y: newY });
            };

            fitToViewport(); // Chạy ngay lập tức
            
            // Nếu người dùng co kéo cửa sổ trình duyệt, tự động Scale lại cho vừa!
            window.addEventListener('resize', fitToViewport);
            return () => window.removeEventListener('resize', fitToViewport);
        }
    }, [viewportMode, screenData?.size_x, screenData?.size_y]);

    // --- XỬ LÝ SỰ KIỆN ZOOM (WHEEL) ---
    const handleWheel = (e: any) => {
        e.evt.preventDefault();
        
        // Thoát chế độ Full Viewport nếu user chủ động cuộn chuột
        if (viewportMode !== 'normal') {
            setViewportMode('normal');
        }

        const scaleBy = 1.1;
        const stage = stageRef.current;
        const oldScale = stage.scaleX();
        const pointer = stage.getPointerPosition();

        const mousePointTo = { x: (pointer.x - stage.x()) / oldScale, y: (pointer.y - stage.y()) / oldScale };
        const newScale = e.evt.deltaY < 0 ? oldScale * scaleBy : oldScale / scaleBy;

        setScale(newScale);
        setPosition({ x: pointer.x - mousePointTo.x * newScale, y: pointer.y - mousePointTo.y * newScale });
    };

    const handleContextMenu = (e: any) => {

        if (useSequencerStore.getState().isEngineRunning) return; 

        e.evt.preventDefault();
        if (e.target === stageRef.current) {
            selectComponents([]);
            const pos = stageRef.current.getRelativePointerPosition();
            openActionMenu(screenData.id, 'screen', e.evt.clientX, e.evt.clientY, pos.x, pos.y);
        }
    };

    const handleDragStart = (e: any) => {
        // Thoát chế độ Full Viewport nếu user chủ động nhấp kéo nền Canvas (Pan)
        if (e.target === stageRef.current && viewportMode !== 'normal') {
            setViewportMode('normal');
        }
    };

    return (
        <div 
            ref={containerRef} // Cắm Ref vào đây để đo kích thước vùng chứa
            className="flex-1 h-full relative bg-[#202124] overflow-hidden" 
            onContextMenu={(e) => e.preventDefault()} 
            onClick={closeActionMenu}
        >
            <div className="absolute inset-0 z-0 pointer-events-none opacity-10" 
                 style={{ backgroundImage: 'radial-gradient(circle, #8ab4f8 1px, transparent 1px)', backgroundSize: '24px 24px' }}>
            </div>

            {screenData && (
                <Stage 
                    width={window.innerWidth} 
                    height={window.innerHeight} 
                    ref={stageRef} 
                    scaleX={scale} 
                    scaleY={scale} 
                    x={position.x} 
                    y={position.y}
                    draggable={true} // Bật tính năng Pan (Kéo toàn bộ canvas)
                    onDragStart={handleDragStart} // Lắng nghe sự kiện bắt đầu kéo
                    onWheel={handleWheel}
                    onContextMenu={handleContextMenu}
                    onClick={(e) => { if(e.target === stageRef.current) selectComponents([]); }}
                >
                    <Layer>
                        <Rect 
                            width={screenData.size_x} 
                            height={screenData.size_y} 
                            stroke="#3c4043" 
                            strokeWidth={2} 
                            fill={screenBgColor} 
                            listening={false} 
                        />
                        
                        {screenData.children_id?.map((childId: string) => (
                            <SceneNodeRenderer key={childId} id={childId} />
                        ))}
                    </Layer>
                </Stage>
            )}
        </div>
    );
};