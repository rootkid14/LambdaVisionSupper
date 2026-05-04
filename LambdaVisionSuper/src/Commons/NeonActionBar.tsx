export interface ActionItem {
  id: string;
  label: string;
  icon: any;
  activeColor: 'cyan' | 'emerald' | 'purple' | 'blue' | 'orange';
  onClick: () => void;
}

interface NeonActionBarProps {
  items: ActionItem[];
  activeId?: string | null;
  className?: string;
}

export const NeonActionBar = ({ items, activeId = null, className = "" }: NeonActionBarProps) => {

  // 1. Style khi đang CHỌN (Active) -> Sáng rực rỡ, nền đậm
  const getActiveStyles = (colorName: string) => {
    switch (colorName) {
      case 'cyan': return 'bg-cyan-600 text-white shadow-[0_0_20px_rgba(8,145,178,0.5)] border-cyan-400/50';
      case 'emerald': return 'bg-emerald-600 text-white shadow-[0_0_20px_rgba(5,150,105,0.5)] border-emerald-400/50';
      case 'purple': return 'bg-purple-600 text-white shadow-[0_0_20px_rgba(147,51,234,0.5)] border-purple-400/50';
      case 'orange': return 'bg-orange-600 text-white shadow-[0_0_20px_rgba(249,115,22,0.5)] border-orange-400/50';
      default: return 'bg-blue-600 text-white shadow-[0_0_20px_rgba(37,99,235,0.5)] border-blue-400/50';
    }
  };

  // 2. Style khi HOVER (Chưa chọn) -> Nền mờ hơn một chút để phân biệt, nhưng Glow vẫn giữ nguyên
  const getHoverStyles = (colorName: string) => {
    switch (colorName) {
      case 'cyan': return 'hover:bg-cyan-600/50 hover:text-white hover:shadow-[0_0_20px_rgba(8,145,178,0.5)] hover:border-cyan-400/50 border-transparent';
      case 'emerald': return 'hover:bg-emerald-600/50 hover:text-white hover:shadow-[0_0_20px_rgba(5,150,105,0.5)] hover:border-emerald-400/50 border-transparent';
      case 'purple': return 'hover:bg-purple-600/50 hover:text-white hover:shadow-[0_0_20px_rgba(147,51,234,0.5)] hover:border-purple-400/50 border-transparent';
      case 'orange': return 'hover:bg-orange-600/50 hover:text-white hover:shadow-[0_0_20px_rgba(249,115,22,0.5)] hover:border-orange-400/50 border-transparent';
      default: return 'hover:bg-blue-600/50 hover:text-white hover:shadow-[0_0_20px_rgba(37,99,235,0.5)] hover:border-blue-400/50 border-transparent';
    }
  };

  return (
    <div className={`flex items-center p-2 bg-slate-950/40 backdrop-blur-xl border border-slate-700/50 rounded-xl shadow-[0_8px_32px_rgba(0,0,0,0.5)] ${className}`}>
      
      {items.map((item) => {
        const Icon = item.icon;
        const isActive = activeId === item.id;

        return (
          <button
            key={item.id}
            onClick={item.onClick}
            className={`
              group /* THÊM GROUP ĐỂ BẮT SỰ KIỆN HOVER CHO ICON VÀ VIỀN */
              relative flex items-center justify-center gap-3 
              px-6 py-4 min-w-[180px] 
              rounded-lg font-mono font-bold text-sm tracking-wide
              transition-all duration-300 ease-out border
              ${
                isActive 
                  ? getActiveStyles(item.activeColor) 
                  // Khi inactive: Kết hợp màu chữ xám, hover nảy nhẹ, và hàm getHoverStyles
                  : `text-slate-400 hover:-translate-y-1 ${getHoverStyles(item.activeColor)}`
              }
            `}
          >
            {/* Icon: Đang active thì nháy liên tục, chưa active thì hover vào mới nháy */}
            <Icon size={18} className={isActive ? 'animate-pulse' : 'group-hover:animate-pulse'} />
            
            {item.label}
            
          </button>
        );
      })}
    </div>
  );
};