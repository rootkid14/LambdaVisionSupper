// Pages/ProgrammingTab.tsx
import { useCallback, useEffect, useState, useRef } from 'react';
import { ReactFlow, Background, BackgroundVariant, ReactFlowInstance, NodeTypes, SelectionMode, Connection } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { useFlowStore } from '../Stores/FlowStore';
import { NodeContextMenu } from '../components/ProgramMode/NodesMenu';
import { DebugPanel } from '../components/ProgramMode/DebugPanel';
import { UniversalNode } from '../components/ProgramMode/ProgrammingNode';
import { DynamicTerminalNode } from '../components/ProgramMode/DynamicTerminalNode';
import { JsonBuilderNode } from '../components/ProgramMode/JsonBuilderNode';
import { JsonExtractorNode } from '../components/ProgramMode/JsonExtractorNode';
import { ObjectNodeUI } from '../components/ProgramMode/ObjectNodeIUI';
import { DynamicSwitchNode } from '../components/ProgramMode/DynamicUniversalSwitchNode';
import { DynamicMemoryNode } from '../components/ProgramMode/DynamicMemoryNode';
import { MemoryReadNode } from '../components/ProgramMode/MemoryReadNode';
import { InlineNode } from '../components/ProgramMode/InLineNode';
import { FlowControlNode } from '../components/ProgramMode/FlowControlNode';
import { TeleportNodeUI } from '../components/ProgramMode/TeleportNodes';

// CƠ CHẾ ROUTER THÔNG MINH CHO CÁC KHỐI NODE LỚP PROGRAM (TYPE "1")
const Type1Router = (props: any) => {
  const { className } = props.data;
  
  if (className === 'CreateJSONNode') return <JsonBuilderNode {...props} />;
  if (className === 'ExtractJSONNode') return <JsonExtractorNode {...props} />;
  if (className === 'ReceivePayloadNode' || className === 'SendResponseNode') return <DynamicTerminalNode {...props} />;
  
  // Mapping trực tiếp Dynamic Switch từ Backend vào Graphic Component
  if (className === 'DynamicUniversalSwitchNode') return <DynamicSwitchNode {...props} />;
  
  return <UniversalNode {...props} />;
};

const nodeTypes: NodeTypes = {
    "1": Type1Router as any,
    "2": InlineNode as any,      
    "3": ObjectNodeUI as any, 
    "4": UniversalNode as any, 
    "5": UniversalNode as any, 
    "6": FlowControlNode as any, 
    "7": FlowControlNode as any, 
    '8': DynamicMemoryNode as any,
    '9': MemoryReadNode as any,
    '10': TeleportNodeUI as any,
    '11': TeleportNodeUI as any,
};

export const ProgrammingTab = () => {
  const {
    nodes, edges, onNodesChange, onEdgesChange, onConnect,
    addNode, updateNodeData, loadNodeCatalogue, isCatalogueLoaded, this_worker_infor, copySelection, pasteSelection,
    takeSnapshot, undo, redo
  } = useFlowStore();

  const [rfInstance, setRfInstance] = useState<ReactFlowInstance | null>(null);
  const [menu, setMenu] = useState({ isOpen: false, screenY: 0, screenX: 0, canvasPos: { x: 0, y: 0 } });

  useEffect(() => {
    if (this_worker_infor?.selected_worker_id && !isCatalogueLoaded) {
      loadNodeCatalogue();
    }
  }, [this_worker_infor, isCatalogueLoaded, loadNodeCatalogue]);

  const lastMousePos = useRef({ x: 0, y: 0 });

  // LẮNG NGHE SỰ KIỆN CHUỘT VÀ BÀN PHÍM (COPY, PASTE, UNDO, REDO)
  useEffect(() => {
    // 1. Theo dõi tọa độ chuột liên tục trên toàn màn hình (Dành cho Paste)
    const handleMouseMove = (e: MouseEvent) => {
      lastMousePos.current = { x: e.clientX, y: e.clientY };
    };
    
    // 2. Định tuyến các tổ hợp phím tắt
    const handleKeyDown = (e: KeyboardEvent) => {
      // BỎ QUA NẾU ĐANG GÕ TEXT: Tránh cướp phím nếu đang gõ văn bản trong các ô input
      if (
        e.target instanceof HTMLInputElement || 
        e.target instanceof HTMLTextAreaElement || 
        e.target instanceof HTMLSelectElement
      ) {
        return;
      }

      // Hỗ trợ cả phím Ctrl (Windows) và Cmd (Mac)
      const isCmdOrCtrl = e.ctrlKey || e.metaKey;

      // ==========================================
      // NHÓM LỆNH COPY & PASTE
      // ==========================================
      if (isCmdOrCtrl && e.key.toLowerCase() === 'c') {
        e.preventDefault();
        copySelection();
      }

      if (isCmdOrCtrl && e.key.toLowerCase() === 'v') {
        e.preventDefault();
        
        // Quy đổi tọa độ màn hình sang tọa độ Canvas của React Flow
        let flowPos = undefined;
        if (rfInstance) {
          flowPos = rfInstance.screenToFlowPosition({
            x: lastMousePos.current.x,
            y: lastMousePos.current.y
          });
        }
        
        // Paste và dời cụm Node tới vị trí chuột
        pasteSelection(flowPos);
      }

      // ==========================================
      // NHÓM LỆNH UNDO & REDO
      // ==========================================
      if (isCmdOrCtrl && e.key.toLowerCase() === 'z') {
        e.preventDefault();
        if (e.shiftKey) {
          redo(); // Bấm Ctrl + Shift + Z
        } else {
          undo(); // Bấm Ctrl + Z
        }
      }

      if (isCmdOrCtrl && e.key.toLowerCase() === 'y') {
        e.preventDefault();
        redo(); // Bấm Ctrl + Y
      }
    };

    // Đăng ký Event Listeners
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('keydown', handleKeyDown);
    
    // Clean up: Gỡ bỏ event khi Component bị unmount để chống rò rỉ bộ nhớ (Memory Leak)
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [copySelection, pasteSelection, undo, redo, rfInstance]);

  // CƠ CHẾ EDGE VALIDATION CHO HỆ THỐNG DÂY (STRICT RULES)
  const handleConnect = useCallback((params: Connection) => {
    const sourceNode = nodes.find(n => n.id === params.source);
    const targetNode = nodes.find(n => n.id === params.target);
    
    if (sourceNode && targetNode) {
      let sourcePinType = 'any';
      let targetPinType = 'any';
      
      const sourceOutputs = (sourceNode.data?.outputs as any[]) || [];
      const sourceCases = (sourceNode.data?.cases as any[]) || [];
      
      const sourcePin = sourceOutputs.find((p: any) => p.id === params.sourceHandle) ||
                        sourceCases.map((_:any, i:number) => ({id: `out_case_${i}`, dataType: 'execute'})).find((p:any) => p.id === params.sourceHandle) ||
                        (params.sourceHandle === 'out_default' ? {dataType: 'execute'} : null);
                        
      if (sourcePin) sourcePinType = sourcePin.dataType;
      
      const targetInputs = (targetNode.data?.inputs as any[]) || [];
      const targetPin = targetInputs.find((p: any) => p.id === params.targetHandle);
      
      if (targetPin) targetPinType = targetPin.dataType;

      const isSourceAny = sourcePinType === 'any';
      const isTargetAny = targetPinType === 'any';
      const isSourceExec = sourcePinType === 'execute';
      const isTargetExec = targetPinType === 'execute';

      let isValid = false;
      
      if (isSourceExec || isTargetExec) {
         if (isSourceExec && isTargetExec) isValid = true;
      } else if (isSourceAny || isTargetAny) {
         isValid = true;
      } else if (sourcePinType === targetPinType) {
         isValid = true;
      }
      
      if (!isValid) {
         alert(`Lỗi nối dây: Không thể kết nối tín hiệu kiểu [${sourcePinType.toUpperCase()}] sang cổng [${targetPinType.toUpperCase()}].`);
         return; 
      }

      if (sourcePinType === 'execute') {
          const existingEdges = edges.filter(
              e => e.source === params.source && e.sourceHandle === params.sourceHandle
          );
          const isSplitNode = sourceNode.type === '7';
          if (existingEdges.length >= 1 && !isSplitNode) {
              alert("Lỗi nối dây: Khối thông thường chỉ được phép có 1 kết nối Execute Out. Sử dụng khối SPLIT nếu muốn rẽ nhánh luồng!");
              return;
          }
      }
      
      if (targetPinType !== 'execute') {
          const existingTargetEdges = edges.filter(
              e => e.target === params.target && e.targetHandle === params.targetHandle
          );
          if (existingTargetEdges.length >= 1) {
              alert("Lỗi nối dây: Cổng nhập dữ liệu (Data Input) chỉ được nhận 1 luồng kết nối.");
              return;
          }
      }
    }

    onConnect(params);
    updateNodeData(params.source, { errorMessage: undefined });
    updateNodeData(params.target, { errorMessage: undefined });
    
  }, [onConnect, updateNodeData, nodes, edges]);

  const handleAddNode = useCallback((template: any) => {
    const isReceiveNode = template.class === 'ReceivePayloadNode';
    const isSendNode = template.class === 'SendResponseNode';

    if (isReceiveNode && nodes.some(n => n.data?.className === 'ReceivePayloadNode')) {
      alert("⚠️ Hệ thống chỉ cho phép tồn tại duy nhất MỘT node Data In (ReceivePayload).");
      setMenu(m => ({ ...m, isOpen: false }));
      return;
    }
    
    if (isSendNode && nodes.some(n => n.data?.className === 'SendResponseNode')) {
      alert("⚠️ Hệ thống chỉ cho phép tồn tại duy nhất MỘT node Data Out (SendResponse).");
      setMenu(m => ({ ...m, isOpen: false }));
      return;
    }

    addNode({
      id: `${template.class}-${Date.now()}`,
      type: template.type,
      position: menu.canvasPos,
      data: { ...template, className: template.class, displayName: template.label }
    });
    setMenu(m => ({ ...m, isOpen: false }));
  }, [menu.canvasPos, addNode, nodes]);

  return (
    // Sử dụng màu nền chuẩn Chrome Dark Theme: #202124
    <div className="relative w-full h-screen flex font-sans" style={{ backgroundColor: '#202124' }}>
      <DebugPanel/>
      <div className="flex-1 relative">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={handleConnect}
          onInit={setRfInstance}
          onNodeDragStart={() => takeSnapshot()} // Chụp ảnh ngay lúc NHẤC chuột lên kéo Node
          onNodesDelete={() => takeSnapshot()}   // Chụp ảnh trước khi Xóa Node
          onEdgesDelete={() => takeSnapshot()}
          onPaneContextMenu={(e) => { 
            e.preventDefault(); 
            setMenu({ 
              isOpen: true, 
              screenX: e.clientX, 
              screenY: e.clientY, 
              canvasPos: rfInstance!.screenToFlowPosition({ x: e.clientX, y: e.clientY }) 
            }); 
          }}
          onPaneClick={() => setMenu(m => ({ ...m, isOpen: false }))}
          deleteKeyCode={["Delete", "Backspace"]}
          fitView
          // Áp dụng màu nền nền Canvas chuẩn Google Dark Mode
          style={{ backgroundColor: '#202124' }} 
          panOnDrag={[1, 2]} 
          selectionOnDrag={true} 
          selectionMode={SelectionMode.Partial} 
        >
          <Background
              variant={BackgroundVariant.Dots}
              // Dùng màu xám Chrome text secondary (#9aa0a6) với low opacity cho các chấm bi (Dots)
              color="rgba(154, 160, 166, 0.15)" 
              gap={20} // Tăng khoảng cách chấm bi lên chút xíu cho đỡ rối mắt
              size={1.5} 
          />
        </ReactFlow>
      </div>
      <NodeContextMenu isOpen={menu.isOpen} screenX={menu.screenX} screenY={menu.screenY} onSelectNode={handleAddNode} />
    </div>
  );
};