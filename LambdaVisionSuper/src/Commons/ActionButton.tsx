import { ReactNode } from "react";

// Định nghĩa kiểu dữ liệu cho Props
interface ActionButtonProps {
  label: string;
  color?: "default" | "blue" | "red" | "emerald" | "orange";
  icon?: ReactNode;
  className?: string;
  onClick?: () => void;
}

export const ActionButton = ({ 
  label, 
  color = "default", 
  icon, 
  className = "", 
  onClick 
}: ActionButtonProps) => {
    const colors = {
        default: "bg-slate-700 hover:bg-slate-600 border-slate-600 text-slate-100",
        blue: "bg-blue-600 hover:bg-blue-500 border-blue-400",
        red: "bg-rose-600 hover:bg-rose-500 border-rose-400",
        emerald: "bg-emerald-600 hover:bg-emerald-500 border-emerald-400",
        orange: "bg-orange-600 hover:bg-orange-500 border-orange-400"
    };

    return (
        <button 
            onClick={onClick}
            className={`${colors[color]} ${className} text-white px-3 py-1.5 rounded-lg border-b-4 active:border-b-0 active:translate-y-1 font-bold text-xs sm:text-sm flex justify-center items-center gap-2 transition-all shadow-[0_0_15px_rgba(0,0,0,0.5)] hover:shadow-[0_0_20px_inherit] whitespace-nowrap`}
        >
            {icon}
            {label}
        </button>
    );
};