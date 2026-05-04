// File: src/utils/FlowCompiler.ts
import { Node, Edge } from '@xyflow/react';
import { UniversalNodeData, PinData } from '../components/ProgramMode/ProgrammingNode'; 

export const FlowCompiler = {
  compile: (nodes: Node[], edges: Edge[]) => {
    const nodeErrors: Record<string, string> = {};

    const formattedNodes = nodes.map(node => {
      const data = node.data as unknown as UniversalNodeData;
      
      // 1. KIỂM TRA KẾT NỐI BẮT BUỘC
      data.inputs?.forEach((input: PinData) => {
        if (input.optional) return;
        const isConnected = edges.some(e => e.target === node.id && e.targetHandle === input.id);
        if (!isConnected) nodeErrors[node.id] = `Cổng [${input.label}] yêu cầu kết nối.`;
      });

      // 2. KIỂM TRA KHỐI ĐẦU VÀO
      if (data.className === 'ReceivePayloadNode') {
        const hasOutgoingConnection = edges.some(e => e.source === node.id);
        if (!hasOutgoingConnection) {
          nodeErrors[node.id] = "Khối [Data In] chưa được cắm vào bất kỳ logic xử lý nào.";
        }
      }

      // 3. KIỂM TRA KHỐI ĐẦU RA
      if (data.className === 'SendResponseNode') {
        const hasPins = data.inputs && data.inputs.length > 0;
        if (!hasPins) {
          nodeErrors[node.id] = "Khối [Data Out] cần ít nhất một cổng đầu vào để định nghĩa dữ liệu trả về.";
        }
        
        const hasIncomingConnection = edges.some(e => e.target === node.id);
        if (hasPins && !hasIncomingConnection) {
          nodeErrors[node.id] = "Khối [Data Out] đã định nghĩa cổng nhưng chưa có dữ liệu cắm vào.";
        }
      }

      // FORMAT DỮ LIỆU SẠCH CHO BACKEND
      return {
        id: node.id,
        type: data.nodeType || "1",
        class: data.className,
        data: {
          displayName: data.displayName,
          inputs: data.inputs || [],
          outputs: data.outputs || [],
          inlineInputType: data.inlineInputType,
          inlineValue: data.inlineValue
        }
      };
    });

    // BACKEND KHÔNG CẦN EDGE ID, CHỈ CẦN BIẾT AI NỐI VỚI AI
    const formattedEdges = edges.map(edge => ({
      source: edge.source,
      sourceHandle: edge.sourceHandle,
      target: edge.target,
      targetHandle: edge.targetHandle
    }));

    return {
      success: Object.keys(nodeErrors).length === 0,
      nodeErrors,
      workflow: {
        nodes: formattedNodes,
        edges: formattedEdges
      }
    };
  }
};