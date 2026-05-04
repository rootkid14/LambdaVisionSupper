import { useState } from 'react';
import { X, Server, Network, Loader2, PlugZap, Save, AlertTriangle } from 'lucide-react';

export const AddWorkerModal = ({ onClose, onSubmit }: { onClose: () => void, onSubmit: (id: string, host: string) => Promise<void> }) => {
  const [id, setId] = useState('');
  const [host, setHost] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    setIsSubmitting(true);
    await onSubmit(id, host);
    setIsSubmitting(false);
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[60] flex items-center justify-center p-4 font-sans">
      <div className="bg-[#28292c] border border-[#3c4043] rounded-2xl w-full max-w-md shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        <div className="px-6 py-4 border-b border-[#3c4043] flex justify-between items-center bg-[#303134]">
          <h3 className="font-bold text-lg text-[#e8eaed] flex items-center gap-2"><Server className="text-[#8ab4f8]"/> Register New Worker</h3>
          <button onClick={onClose} className="text-[#9aa0a6] hover:text-[#f28b82] transition-colors"><X size={20}/></button>
        </div>
        <div className="p-6 flex flex-col gap-4">
          <div>
            <label className="block text-xs font-bold text-[#9aa0a6] uppercase mb-2">Server ID (Unique)</label>
            <input type="text" placeholder="e.g., worker_line_3" value={id} onChange={(e) => setId(e.target.value)} className="w-full bg-[#171717] border border-[#3c4043] text-[#e8eaed] rounded-lg px-4 py-2.5 focus:outline-none focus:border-[#8ab4f8] focus:ring-1 focus:ring-[#8ab4f8] transition-colors" />
          </div>
          <div>
            <label className="block text-xs font-bold text-[#9aa0a6] uppercase mb-2">Host Address</label>
            <input type="text" placeholder="192.168.1.x:8000" value={host} onChange={(e) => setHost(e.target.value)} className="w-full bg-[#171717] border border-[#3c4043] text-[#e8eaed] rounded-lg px-4 py-2.5 focus:outline-none focus:border-[#8ab4f8] focus:ring-1 focus:ring-[#8ab4f8] transition-colors font-mono" />
          </div>
        </div>
        <div className="px-6 py-4 border-t border-[#3c4043] bg-[#202124] flex justify-end gap-3">
          <button onClick={onClose} className="px-4 py-2 rounded-lg text-[#9aa0a6] font-semibold hover:bg-[#3c4043] hover:text-[#e8eaed] transition-colors">Cancel</button>
          <button onClick={handleSubmit} disabled={isSubmitting || !id || !host} className="flex items-center gap-2 px-6 py-2 bg-[#8ab4f8] hover:bg-[#aecbfa] text-[#202124] rounded-lg font-bold transition-colors disabled:opacity-50">
            {isSubmitting ? <Loader2 size={18} className="animate-spin" /> : <Network size={18} />}
            {isSubmitting ? 'Connecting...' : 'Connect to Bus'}
          </button>
        </div>
      </div>
    </div>
  );
};

export const SwitchMasterModal = ({ currentHost, onClose, onSwitch }: { currentHost: string | null, onClose: () => void, onSwitch: (host: string) => void }) => {
  const [host, setHost] = useState(currentHost || '');

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[60] flex items-center justify-center p-4 font-sans">
      <div className="bg-[#28292c] border border-[#3c4043] rounded-2xl w-full max-w-md shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        <div className="px-6 py-4 border-b border-[#3c4043] flex justify-between items-center bg-[#303134]">
          <h3 className="font-bold text-lg text-[#e8eaed] flex items-center gap-2"><PlugZap className="text-[#8ab4f8]"/> Master Connection</h3>
          <button onClick={onClose} className="text-[#9aa0a6] hover:text-[#f28b82] transition-colors">
              <X size={20} />
          </button>
        </div>
        <div className="p-6 flex flex-col gap-4">
          <p className="text-sm text-[#9aa0a6] mb-2">Đổi địa chỉ Master Gateway để HMI trỏ tới hệ thống khác. HMI sẽ tải lại toàn bộ cấu hình.</p>
          <div>
            <label className="block text-xs font-bold text-[#9aa0a6] uppercase mb-2">Master API Endpoint</label>
            <input type="text" placeholder="http://192.168.1.100:8000" value={host} onChange={(e) => setHost(e.target.value)} className="w-full bg-[#171717] border border-[#3c4043] text-[#e8eaed] rounded-lg px-4 py-2.5 focus:outline-none focus:border-[#8ab4f8] focus:ring-1 focus:ring-[#8ab4f8] transition-colors font-mono" />
          </div>
        </div>
        <div className="px-6 py-4 border-t border-[#3c4043] bg-[#202124] flex justify-between items-center">
          <button className="text-xs text-[#9aa0a6] hover:text-[#e8eaed] underline underline-offset-2 flex items-center gap-1"><Save size={14}/> Save to profiles</button>
          <div className="flex gap-3">
            {<button onClick={onClose} className="px-4 py-2 rounded-lg text-[#9aa0a6] font-semibold hover:bg-[#3c4043] hover:text-[#e8eaed] transition-colors">Cancel</button>}
            <button onClick={() => onSwitch(host)} disabled={!host} className="flex items-center gap-2 px-6 py-2 bg-[#8ab4f8] hover:bg-[#aecbfa] text-[#202124] rounded-lg font-bold transition-colors disabled:opacity-50">
              Switch Gateway
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export const ErrorModal = ({ message, onClose }: { message: string | any, onClose: () => void }) => {
  const safeMessage = typeof message === 'string' ? message : JSON.stringify(message, null, 2);

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[60] flex items-center justify-center p-4 font-sans">
      <div className="bg-[#28292c] border border-[#f28b82]/30 rounded-2xl w-full max-w-sm shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        <div className="px-6 py-4 border-b border-[#f28b82]/20 flex items-center gap-2 bg-[#f28b82]/10">
          <AlertTriangle className="text-[#f28b82]" />
          <h3 className="font-bold text-lg text-[#e8eaed]">System Error</h3>
        </div>
        
        <div className="p-6 text-[#e8eaed] text-sm break-words whitespace-pre-wrap">
          {safeMessage}
        </div>
        
        <div className="px-6 py-4 border-t border-[#3c4043] flex justify-end bg-[#202124]">
          <button onClick={onClose} className="px-6 py-2 bg-[#303134] hover:bg-[#3c4043] text-[#e8eaed] border border-[#3c4043] rounded-lg font-bold transition-colors">OK</button>
        </div>
      </div>
    </div>
  );
};