import { DivideIcon as LucideIcon } from 'lucide-react';

// 1. Định nghĩa kiểu dữ liệu cho MỘT nút bấm
export interface NavItem {
  id: string;
  label: string;
  icon: typeof LucideIcon; // Kiểu dữ liệu chuẩn cho icon của thư viện lucide-react
}

// 2. Định nghĩa Props truyền vào cho toàn bộ Navbar
interface NeonNavbarProps {
  items: NavItem[];          // Danh sách các nút
  activeId: string;          // ID của nút đang được chọn
  onTabChange: (id: string) => void; // Hàm trigger khi bấm nút
  className?: string;        // Cho phép custom thêm CSS từ bên ngoài nếu cần
}

export const NeonNavbar = ({ items, activeId, onTabChange, className = "" }: NeonNavbarProps) => {
  return (
    <div className={`flex items-center p-2 bg-slate-950/40 backdrop-blur-xl border border-slate-700/50 rounded-xl shadow-[0_8px_32px_rgba(0,0,0,0.5)] ${className}`}>
      
      {items.map((item) => {
        const Icon = item.icon;
        const isActive = activeId === item.id;

        return (
          <button
            key={item.id}
            onClick={() => onTabChange(item.id)}
            className={`
              relative flex items-center justify-center gap-3 
              px-6 py-4 min-w-[180px] rounded-lg 
              font-mono font-bold text-sm tracking-wide
              transition-all duration-300 ease-out border border-transparent
              ${
                isActive 
                  // TRẠNG THÁI ACTIVE: Màu Tím Neon
                  ? 'bg-purple-600 text-white shadow-[0_0_20px_rgba(168,85,247,0.6)] border-purple-400/50' 
                  // TRẠNG THÁI INACTIVE: Tối màu, kính mờ, chỉ sáng lên khi hover
                  : 'text-slate-400 hover:text-purple-200 hover:bg-slate-800/60' 
              }
            `}
          >
            {/* Nếu đang active thì icon nhấp nháy nhẹ (pulse), không thì đứng im */}
            <Icon size={18} className={isActive ? 'animate-pulse text-white' : 'text-slate-500'} />
            
            {item.label}

            {/* Vệt sáng 3D trên đỉnh nút (chỉ hiện khi Active) */}
            {isActive && (
              <div className="absolute top-0 left-0 w-full h-[1px] bg-white/50 rounded-t-lg"></div>
            )}
          </button>
        );
      })}
    </div>
  );
};