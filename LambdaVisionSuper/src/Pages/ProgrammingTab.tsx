// components/ProgrammingTab.tsx
import { useCallback, useEffect, useState } from 'react';
import { ReactFlow, Background, BackgroundVariant, ReactFlowInstance, NodeTypes, SelectionMode } from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { useFlowStore } from '../Stores/FlowStore';
import { NodeContextMenu } from '../components/ProgramMode/NodesMenu';
import { DebugPanel } from '../components/ProgramMode/DebugPanel';

import { UniversalNode } from '../components/ProgramMode/ProgrammingNode';
import { DynamicTerminalNode } from '../components/ProgramMode/DynamicTerminalNode';
import { JsonBuilderNode } from '../components/ProgramMode/JsonBuilderNode';
import { JsonExtractorNode } from '../components/ProgramMode/JsonExtractorNode';
import { ObjectNodeUI } from '../components/ProgramMode/ObjectNodeIUI';

// CƠ CHẾ ROUTER THÔNG MINH CHO TYPE "1"
const Type1Router = (props: any) => {
  const { className } = props.data;
  if (className === 'CreateJSONNode') return <JsonBuilderNode {...props} />;
  if (className === 'ExtractJSONNode') return <JsonExtractorNode {...props} />;
  if (className === 'ReceivePayloadNode' || className === 'SendResponseNode') return <DynamicTerminalNode {...props} />;
  return <UniversalNode {...props} />;
};

const nodeTypes: NodeTypes = { 
    "1": Type1Router as any,
    "2": UniversalNode as any, // InlineNode
    "3": ObjectNodeUI as any,  // ObjectNode
    "4": UniversalNode as any, // FunctionNode
    "5": UniversalNode as any, // APINode
};

export const ProgrammingTab = () => {
  const { 
    nodes, edges, onNodesChange, onEdgesChange, onConnect, 
    addNode, updateNodeData, loadNodeCatalogue, isCatalogueLoaded, this_worker_infor 
  } = useFlowStore();
  const [rfInstance, setRfInstance] = useState<ReactFlowInstance | null>(null);
  const [menu, setMenu] = useState({ isOpen: false, screenY: 0, screenX: 0, canvasPos: { x: 0, y: 0 } });

  useEffect(() => {
    // Chỉ gọi API khi đã xác định được Worker đang chọn VÀ chưa load catalog bao giờ
    if (this_worker_infor?.selected_worker_id && !isCatalogueLoaded) {
      loadNodeCatalogue();
    }
  }, [this_worker_infor, isCatalogueLoaded, loadNodeCatalogue]);

  // Xóa lỗi khi nối dây
  const handleConnect = useCallback((params: any) => {
    onConnect(params);
    updateNodeData(params.source, { errorMessage: undefined });
    updateNodeData(params.target, { errorMessage: undefined });
  }, [onConnect, updateNodeData]);

  const handleAddNode = useCallback((template: any) => {
    const isReceiveNode = template.class === 'ReceivePayloadNode';
    const isSendNode = template.class === 'SendResponseNode';

    // KIỂM TRA PHÒNG THỦ
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

    // NẾU HỢP LỆ THÌ THÊM NODE VÀO STORE
    addNode({
      id: `${template.class}-${Date.now()}`,
      type: template.type,
      position: menu.canvasPos,
      data: { ...template, className: template.class, displayName: template.label }
    });
    setMenu(m => ({ ...m, isOpen: false }));
  }, [menu.canvasPos, addNode, nodes]);

  return (
    // THAY ĐỔI: Chuyển bg-slate-950 sang màu #202124 và thêm màu selection text
    <div className="relative w-full h-screen bg-[#202124] flex selection:bg-[#8ab4f8]/30 font-sans text-[#e8eaed]">
      <DebugPanel/>
      <ReactFlow 
        nodes={nodes} 
        edges={edges} 
        nodeTypes={nodeTypes} 
        onNodesChange={onNodesChange} 
        onEdgesChange={onEdgesChange} 
        onConnect={handleConnect} 
        onInit={setRfInstance}
        onPaneContextMenu={(e) => { e.preventDefault(); setMenu({ isOpen: true, screenX: e.clientX, screenY: e.clientY, canvasPos: rfInstance!.screenToFlowPosition({ x: e.clientX, y: e.clientY }) }); }}
        onPaneClick={() => setMenu(m => ({ ...m, isOpen: false }))} 
        deleteKeyCode={["Delete", "Backspace"]} 
        fitView
        // Đảm bảo background của component ReactFlow trùng màu viền
        style={{ backgroundColor: '#202124' }}
        panOnDrag={[1, 2]} // 1 = Chuột giữa, 2 = Chuột phải để kéo Canvas
        selectionOnDrag={true} // Chuột trái kéo để tạo Selection Box (Lasso)
        selectionMode={SelectionMode.Partial} // Quét trúng 1 góc Node là chọn luôn
      >
        {/* THAY ĐỔI: Dùng đường kẻ Line màu #3c4043 chuẩn UI Dark Mode thay vì màu xanh tím */}
        <Background 
            variant={BackgroundVariant.Dots} 
            color="rgba(255,255,255,0.15)" // Chỉnh màu chấm bi sáng lên một chút cho dễ nhìn
            gap={16} // Khoảng cách giữa các chấm (Mặc định là 16)
            size={1.5} // Kích thước của mỗi chấm
        />
        
      </ReactFlow>
      <NodeContextMenu isOpen={menu.isOpen} screenX={menu.screenX} screenY={menu.screenY} onSelectNode={handleAddNode} />
    </div>
  );
};