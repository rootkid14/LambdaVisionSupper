import { Node, Edge } from '@xyflow/react';
import { UniversalNodeData, PinData } from '../components/ProgramMode/ProgrammingNode';

export const FlowCompiler = {
    compile: (nodes: Node[], edges: Edge[], graph_timeout: number = 30.0) => {
        const nodeErrors: Record<string, string> = {};
        
        const formattedNodes = nodes.map(node => {
            const data = node.data as unknown as UniversalNodeData;
            
            // 1. KIỂM TRA KẾT NỐI BẮT BUỘC
            data.inputs?.forEach((input: PinData) => {
                // Nếu backend đã báo đây là chân tuỳ chọn -> Bỏ qua
                if (input.optional) return;
                
                // [NÂNG CẤP] Đặc quyền cho PortalInNode: Chân payload được phép lơ lửng
                if (data.className === 'PortalInNode' && input.id === 'payload') return;

                const isConnected = edges.some(e => e.target === node.id && e.targetHandle === input.id);
                if (!isConnected) nodeErrors[node.id] = `Cổng [${input.label}] yêu cầu kết nối.`;
            });

            // 2. KIỂM TRA KHỐI ĐẦU VÀO
            if (data.className === 'ReceivePayloadNode') {
                const hasOutgoingConnection = edges.some(e => e.source === node.id);
                if (!hasOutgoingConnection) {
                    nodeErrors[node.id] = "Khối [Data In] chưa được cắm vào logic xử lý nào.";
                }
            }

            // 3. KIỂM TRA KHỐI ĐẦU RA
            if (data.className === 'SendResponseNode') {
                const hasPins = data.inputs && data.inputs.length > 0;
                if (!hasPins) {
                    nodeErrors[node.id] = "Khối [Data Out] cần ít nhất một cổng đầu vào.";
                }
                const hasIncomingConnection = edges.some(e => e.target === node.id);
                if (hasPins && !hasIncomingConnection) {
                    nodeErrors[node.id] = "Khối [Data Out] chưa được kết nối luồng.";
                }
            }

            // CLEAN DATA CHO BACKEND FASTAPI
            const cleanedData = { ...data };
            delete cleanedData.errorMessage;
            delete cleanedData.color;

            return {
                id: node.id,
                type: node.type,
                position: node.position,
                data: cleanedData
            };
        });

        const formattedEdges = edges.map(edge => ({
            id: edge.id,
            source: edge.source,
            sourceHandle: edge.sourceHandle,
            target: edge.target,
            targetHandle: edge.targetHandle
        }));

        if (Object.keys(nodeErrors).length > 0) {
            return { success: false, errors: nodeErrors };
        }

        // TRẢ VỀ PAYLOAD SẠCH HOÀN TOÀN CÓ CHỨA TIMEOUT
        return {
            success: true,
            data: {
                timeout: graph_timeout,
                nodes: formattedNodes, // Chú ý: Đã đổi 'node' thành 'nodes' cho chuẩn định dạng GraphFile
                edges: formattedEdges
            }
        };
    }
};