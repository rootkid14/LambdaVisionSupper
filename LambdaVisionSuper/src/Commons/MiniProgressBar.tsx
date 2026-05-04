
interface MiniProgressBarProps {
  label: string;
  percent: number;
  colorClass: string;
  extraText?: string;
}

export const MiniProgressBar = ({ label, percent, colorClass, extraText }: MiniProgressBarProps) => (
  <div className="flex flex-col gap-1 w-full">
    <div className="flex justify-between text-[10px] font-bold text-slate-400 uppercase">
      <span>{label}</span>
      <span className="text-slate-300">
        {percent?.toFixed(1)}% {extraText && <span className="text-slate-500 font-mono ml-1">({extraText})</span>}
      </span>
    </div>
    <div className="w-full h-1.5 bg-slate-700 rounded-full overflow-hidden">
      <div className={`h-full ${colorClass} transition-all duration-500`} style={{ width: `${percent || 0}%` }}></div>
    </div>
  </div>
);