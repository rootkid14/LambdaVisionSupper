import React, { useState, useCallback, useEffect, useRef } from 'react';
import { ReactFlow, Background, SelectionMode, ReactFlowInstance } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Play, Square, Wrench, AlertTriangle, Cpu, Split, Combine, Shuffle, PlayCircle, StopCircle, ArrowBigLeft, Wifi, Radio } from 'lucide-react';
import { useSequencerStore } from '../UI_Engine/UIEngineStores/SequencerStores';
import { nodeTypes } from '../UI_Engine/SequencerComponents/SequencerNodes';
import { TerminalLog } from '../UI_Engine/SequencerComponents/TerminalLog';
import { PropertiesSidebar } from '../UI_Engine/SequencerComponents/PropertiesSidebar';
import { TokenLayer } from '../UI_Engine/SequencerComponents/TokenLayer';
import { useFleetStore } from '../Stores/FleetDashboardStores';
import { useNavigate } from 'react-router-dom';
import { TagManagerTable } from '../UI_Engine/UIEngineComponents/GlobalTagsTable';


const nodeIcons: Record<string, React.ReactNode> = {
  start: <PlayCircle size={16} className="text-[#81c995]" />,
  end: <StopCircle size={16} className="text-[#f28b82]" />,
  process: <Cpu size={16} />,
  split: <Split size={16} className="rotate-90" />,
  join: <Combine size={16} className="rotate-90" />,
  switch: <Shuffle size={16} />,
  portal_in: <Wifi size={16} className="text-[#c58af9]" />, 
  portal_out: <Radio size={16} className="text-[#fcd663]" />,
};

export const SequencerPage = () => {
  const navigate = useNavigate();
  const store = useSequencerStore();
  const fleetStore = useFleetStore()
  const [rfInstance, setRfInstance] = useState<any>(null);

  const lastMousePos = useRef({ x: 0, y: 0 });
  
  // State quản lý UI mở Sidebar
  const [editingNodeId, setEditingNodeId] = useState<string | null>(null);

  // Lắng nghe sự thay đổi trên Canvas để đánh dấu Dirty (Bắt buộc Compile lại)
  const handleNodesChangeWrapper = useCallback((changes: any) => {
    // Gọi action chuẩn của store để cập nhật tọa độ
    store.onNodesChange(changes);
    
    // Nếu Node đang mở edit bị xóa, đóng panel
    if (changes.some((c: any) => c.type === 'remove' && c.id === editingNodeId)) {
      setEditingNodeId(null);
    }
  }, [editingNodeId, store.onNodesChange]);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      lastMousePos.current = { x: e.clientX, y: e.clientY };
    };

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;

      const isCmdOrCtrl = e.ctrlKey || e.metaKey;

      // COPY / PASTE
      if (isCmdOrCtrl && e.key.toLowerCase() === 'c') {
        e.preventDefault();
        store.copySelection();
      }
      if (isCmdOrCtrl && e.key.toLowerCase() === 'v') {
        e.preventDefault();
        const flowPos = rfInstance?.screenToFlowPosition({
          x: lastMousePos.current.x,
          y: lastMousePos.current.y
        });
        store.pasteSelection(flowPos);
      }

      // UNDO / REDO
      if (isCmdOrCtrl && e.key.toLowerCase() === 'z') {
        e.preventDefault();
        if (e.shiftKey) store.redo();
        else store.undo();
      }
      if (isCmdOrCtrl && e.key.toLowerCase() === 'y') {
        e.preventDefault();
        store.redo();
      }
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [store, rfInstance]);

  useEffect(() => {
    // Chỉ gọi nếu đã có gateway lưu trong LocalStorage
    if (fleetStore.gateway) {
        fleetStore.silentRefreshFleet();
    }
  }, []);

  const addNewNodeAtCenter = (type: any) => {
    let position = { x: 300, y: 150 };

    if (rfInstance) {
        // Lấy tâm màn hình
        const centerX = window.innerWidth / 2;
        const centerY = window.innerHeight / 2;
        // Chuyển đổi sang hệ tọa độ của Graph
        position = rfInstance.screenToFlowPosition({ x: centerX, y: centerY });
    }

    // Gọi hàm trong Store kèm tọa độ vừa tính
    store.addNode(type, position);
};

  const handleCompile = async () => {
    setEditingNodeId(null); // Đóng sidebar khi compile để tránh lỗi
    await store.compileGraph();
  };

  // Hack để truyền hàm onEdit xuống các Node
  const nodesWithProps = store.nodes.map(n => ({
    ...n,
    data: { ...n.data, onEdit: (id: string) => setEditingNodeId(id) }
  }));

  return (
    <div className="h-screen w-screen bg-[#202124] flex flex-col overflow-hidden text-[#e8eaed] font-sans selection:bg-[#8ab4f8]/30 relative">
      
      {/* HEADER BAR */}
      <header className="h-14 bg-[#303134] border-b border-[#3c4043] flex items-center justify-between px-4 z-40 shrink-0 relative">
        <div className="flex items-center gap-4">
          {/* NÚT BACK */}
          <button 
            onClick={() => navigate('/inspection')} 
            className="flex items-center gap-2 p-1.5 hover:bg-violet-400 rounded-2xl bg-[#5e6469] px-5 text-[#ffffff] hover:text-[#e8eaed] transition-colors"
            title="Back to Inspection"
          >
            <ArrowBigLeft size={26} />
          </button>
          
          <div className="flex flex-col">
             <span className="text-[px] font-bold text-[#d9d0da] tracking-widest uppercase">LAMBDA SEQUENCER EDITOR</span>
             <div className="flex items-center gap-2">
                <span className="font-bold text-sm">System_Main.graph</span>
                {store.isGraphDirty && <span className="text-[#fcd663] text-[10px] flex items-center gap-1"><AlertTriangle size={12}/> Uncompiled Changes</span>}
             </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* NÚT COMPILE */}
          <button 
            onClick={handleCompile} 
            disabled={store.isEngineRunning}
            className={`flex items-center gap-2 px-4 py-1.5 text-xs font-bold rounded transition-colors ${store.isGraphDirty ? 'bg-[#fcd663] text-[#202124] hover:bg-[#fde293]' : 'bg-[#3c4043] text-[#9aa0a6]'}`}
          >
            <Wrench size={14} /> COMPILE
          </button>
          
          <div className="w-px h-6 bg-[#5f6368] mx-1"></div>

          {/* NÚT START / STOP ENGINE */}
          {!store.isEngineRunning ? (
            <button 
              onClick={() => store.runEngine()} 
              disabled={store.isGraphDirty || store.isCompiling}
              className="flex items-center gap-2 px-4 py-1.5 bg-[#81c995] text-[#202124] rounded text-xs font-bold hover:bg-[#a8dab5] disabled:opacity-50 transition-colors"
            >
              <Play size={14} fill="currentColor" /> RUN ENGINE
            </button>
          ) : (
            <button 
              onClick={() => store.stopEngine()} 
              className="flex items-center gap-2 px-4 py-1.5 bg-[#f28b82] text-[#202124] rounded text-xs font-bold hover:bg-[#f6aea9] transition-colors shadow-[0_0_15px_rgba(242,139,130,0.5)]"
            >
              <Square size={14} fill="currentColor" /> STOP ENGINE
            </button>
          )}
          
        </div>
      </header>

      {/* === VÙNG CHỨA SIDEBAR & CANVAS (z-index thấp hơn Backdrop) === */}
      <div className="flex-1 flex overflow-hidden relative z-0">
        
        {/* LEFT PALETTE */}
        <aside className="w-48 bg-[#28292c] border-r border-[#3c4043] flex flex-col z-10">
          <div className="p-3 border-b border-[#3c4043]">
            <h3 className="text-[10px] font-bold text-[#9aa0a6] uppercase tracking-widest">Library</h3>
          </div>
          <div className="flex-1 overflow-y-auto p-2 flex flex-col gap-1">
             {/* Duyệt mảng nodeTypes để render nút kéo thả/add */}
             {Object.keys(nodeTypes).map(type => (
               <button key={type} onClick={() => addNewNodeAtCenter(type as any)} className="flex items-center gap-3 px-3 py-2 bg-[#303134] hover:bg-[#3c4043] rounded border border-transparent hover:border-[#8ab4f8] text-[#9aa0a6] hover:text-[#e8eaed] transition-all text-[11px] font-bold uppercase tracking-wider">
                  {nodeIcons[type] || <Cpu size={14}/>} {type}
               </button>
             ))}
          </div>
        </aside>

        {/* MAIN CANVAS */}
        <main className="flex-1 flex flex-col relative bg-[#202124]">
          <div className="flex-1 relative">
            <ReactFlow
              nodes={nodesWithProps}
              edges={store.edges}
              onNodesChange={handleNodesChangeWrapper} 
              onEdgesChange={store.onEdgesChange}      
              onConnect={store.onConnect}              
              onInit={setRfInstance}
              nodeTypes={nodeTypes}
              fitView
              deleteKeyCode={['Backspace', 'Delete']}
              style={{ backgroundColor: '#202124' }}

              onNodeDragStart={() => store.takeSnapshot()} // Lưu snapshot khi bắt đầu kéo
              onNodesDelete={() => store.takeSnapshot()}   // Lưu snapshot trước khi xóa
              onEdgesDelete={() => store.takeSnapshot()}

              // ===============================================
              // NÂNG CẤP UX CHUỘT: QUYỀN NĂNG CỦA REACT FLOW
              // ===============================================
              panOnDrag={[1, 2]} // 1 = Chuột giữa, 2 = Chuột phải để kéo Canvas
              selectionOnDrag={true} // Chuột trái dùng để vẽ Select Box (Lasso)
              selectionMode={SelectionMode.Partial} // Quét trúng 1 phần node là chọn luôn
            >
              <Background color="#5f6368" gap={24} size={1} />
              {store.isEngineRunning && <TokenLayer />}
            </ReactFlow>
          </div>
          <TerminalLog />
        </main>

        {/* =============================================== */}
        {/* DOCKED GLOBAL TAGS (Luôn luôn nằm ở bên phải)   */}
        {/* =============================================== */}
        {/* FIX 1: Tăng độ rộng từ 400px lên 480px để các nút thoải mái */}
        <aside className="w-[480px] shrink-0 z-0">
           {/* FIX 2: Đổi mode="view" thành mode="edit" để hiện nút Thêm/Xóa */}
           <TagManagerTable mode="edit" />
        </aside>
        {/* =============================================== */}
        {/* PROPERTIES OVERLAY (Ưu tiên đè lên Tags Table)  */}
        {/* =============================================== */}
        {editingNodeId && (
          // FIX Ở ĐÂY: Đổi w-[400px] thành w-[480px]
          <div className="absolute top-0 left-0 h-full w-[480px] z-10 shadow-[-15px_0_40px_rgba(0,0,0,0.5)] border-l border-[#8ab4f8]/30">
            <PropertiesSidebar nodeId={editingNodeId} onClose={() => setEditingNodeId(null)} />
          </div>
        )}

      </div>
      {/* (Xóa bỏ hoàn toàn lớp BACKDROP cũ ở cuối file) */}
    </div>
  );
};