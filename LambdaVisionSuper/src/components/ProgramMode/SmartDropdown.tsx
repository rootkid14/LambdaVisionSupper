import { useMemo } from 'react';
import { useFlowStore } from '../../Stores/FlowStore'; 

interface SmartDropdownProps {
  type: string;
  value: any;
  onChange: (val: string) => void;
  id: string;
}

export const SmartDropdown = ({ type, value, onChange, id }: SmartDropdownProps) => {
  // Chọc thẳng vào SSOT (FlowStore) để lấy dữ liệu môi trường của worker hiện tại
  const { this_worker_infor } = useFlowStore();

  // Dùng useMemo để tránh việc map lại mảng không cần thiết mỗi khi re-render
  const options = useMemo(() => {
    if (!this_worker_infor) return [];

    switch (type) {
      case 'server_pool_dropdown':
        // Lấy danh sách server từ localSevsInfo
        return (this_worker_infor.localSevsInfo || []).map((s: any) => ({
          value: s.server_id,
          label: s.server_id
        }));

      case 'device_pool_dropdown':
        // Lấy danh sách device từ DevsInfo
        return (this_worker_infor.DevsInfo || []).map((d: any) => ({
          value: d.device_id,
          label: d.device_id
        }));

      case 'active_logic_dropdown':
        // Lưu ý: Key có thể là "graphs" hoặc "graphs_state" tùy vào việc file API của bạn có map lại tên biến không. 
        // Tôi đang giả định bạn dùng đúng key từ BE trả về là "graphs" (hoặc nếu API map thành "graphs_state" thì bạn tự đổi nhé).
        const graphsObj = this_worker_infor.ResourceInfo?.graphs_state || {};
        
        const activeLogics: string[] = [];
        
        // Quét object graphs để tìm các graph đang chạy trên RAM
        Object.entries(graphsObj).forEach(([graphName, info]: [string, any]) => {
          if (info.inram === true) {
            activeLogics.push(graphName);
          }
        });

        return activeLogics.map((name: string) => ({
          value: name,
          label: name
        }));

      default:
        return [];
    }
  }, [this_worker_infor, type]);

  // Trạng thái 1: Chưa load xong Worker Environment
  if (!this_worker_infor) {
    return <span className="text-[10px] text-slate-500 italic">Đang tải cấu hình...</span>;
  }

  // Trạng thái 2: Worker không có dữ liệu cho dropdown này
  if (options.length === 0) {
    return <span className="text-[10px] text-red-400 italic">Không có dữ liệu</span>;
  }

  // Trạng thái 3: Render Dropdown
  return (
    <select 
      id={id}
      className="nodrag w-full bg-slate-100 text-slate-800 text-xs px-2 py-1.5 rounded border border-slate-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors cursor-pointer"
      value={value || ""}
      onChange={(e) => onChange(e.target.value)}
    >
      <option value="" disabled>-- Chọn --</option>
      {options.map((opt, idx) => (
        <option key={`${opt.value}-${idx}`} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  );
};