import React, { useEffect, useState } from 'react';
import { Activity, X, Clock, MapPin, Database, Target, Tag } from 'lucide-react';
import { useSequencerStore } from '../UIEngineStores/SequencerStores';

export const TokenBlackboard = () => {
    const isTokenBlackboardOpen = useSequencerStore(state => state.isTokenBlackboardOpen);
    const toggleTokenBlackboard = useSequencerStore(state => state.toggleTokenBlackboard);
    const tokens = useSequencerStore(state => state.run_time_token_list);
    const nodesMap = useSequencerStore(state => state.nodes_lookup_map);
    
    // Auto-refresh timer cho cột Uptime
    const [, setTick] = useState(0);
    useEffect(() => {
        let interval: ReturnType<typeof setInterval>; 
        
        if (isTokenBlackboardOpen) {
            interval = setInterval(() => setTick(t => t + 1), 1000);
        }
        return () => clearInterval(interval);
    }, [isTokenBlackboardOpen]);

    if (!isTokenBlackboardOpen) return null;

    const tokenEntries = Object.entries(tokens);

    return (
        // TĂNG KÍCH THƯỚC TỔNG THỂ: w-[850px] h-[450px]
        <div className="absolute bottom-4 left-4 z-50 w-[850px] h-[450px] bg-[#202124] border border-[#3c4043] shadow-2xl rounded-xl flex flex-col font-sans overflow-hidden animate-in fade-in slide-in-from-bottom-4">
            
            {/* HEADER */}
            <div className="bg-[#303134] px-5 py-3 border-b border-[#3c4043] flex items-center justify-between shrink-0">
                <div className="flex items-center gap-3">
                    <Activity size={18} className="text-[#8ab4f8] animate-pulse" />
                    <h3 className="text-[#e8eaed] font-bold text-sm tracking-widest uppercase">
                        Active Tokens Blackboard
                    </h3>
                    <span className="ml-3 bg-[#8ab4f8]/20 text-[#8ab4f8] px-2.5 py-1 rounded text-xs font-bold">
                        TOTAL: {tokenEntries.length}
                    </span>
                </div>
                <button onClick={toggleTokenBlackboard} className="text-[#9aa0a6] hover:text-[#f28b82] transition-colors p-1.5 hover:bg-[#3c4043] rounded">
                    <X size={18} />
                </button>
            </div>

            {/* BẢNG THEO DÕI */}
            <div className="flex-1 overflow-auto custom-scrollbar">
                <table className="w-full text-left text-sm">
                    <thead className="bg-[#28292c] sticky top-0 z-10 border-b border-[#3c4043]">
                        <tr>
                            <th className="p-4 text-[#9aa0a6] font-bold uppercase text-xs w-28">Token ID</th>
                            <th className="p-4 text-[#9aa0a6] font-bold uppercase text-xs w-32">Status</th>
                            <th className="p-4 text-[#9aa0a6] font-bold uppercase text-xs w-48">Current Node</th>
                            <th className="p-4 text-[#9aa0a6] font-bold uppercase text-xs w-24">Uptime</th>
                            <th className="p-4 text-[#9aa0a6] font-bold uppercase text-xs">Labels & History</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-[#3c4043] bg-[#171717]">
                        {tokenEntries.length === 0 ? (
                            <tr>
                                <td colSpan={5} className="p-10 text-center text-[#5f6368] italic text-sm">
                                    No active tokens in the system right now.
                                </td>
                            </tr>
                        ) : (
                            tokenEntries.map(([id, token]) => {
                                const shortId = id.substring(0, 6).toUpperCase();
                                const currentNode = nodesMap[token.node_uuid];
                                const nodeName = currentNode ? (currentNode.data?.name || currentNode.type) : "Unknown";
                                const uptimeSecs = Math.floor((Date.now() - (token.spawnedAt || Date.now())) / 1000);
                                
                                return (
                                    <tr key={id} className="hover:bg-[#202124] transition-colors group">
                                        <td className="p-4 font-mono text-[#8ab4f8] font-bold text-sm">#{shortId}</td>
                                        
                                        <td className="p-4">
                                            <span className={`px-2.5 py-1 rounded text-[11px] font-bold uppercase tracking-wider ${
                                                token.status === 'READY' ? 'bg-[#81c995]/20 text-[#81c995] border border-[#81c995]/30' :
                                                token.status === 'PROCESSING' ? 'bg-[#fcd663]/20 text-[#fcd663] border border-[#fcd663]/30' :
                                                token.status === 'WAITING' ? 'bg-[#c58af9]/20 text-[#c58af9] border border-[#c58af9]/30' :
                                                'bg-[#f28b82]/20 text-[#f28b82] border border-[#f28b82]/30'
                                            }`}>
                                                {token.status}
                                            </span>
                                        </td>
                                        
                                        <td className="p-4">
                                            <div className="flex items-center gap-2 text-[#e8eaed] w-full text-sm">
                                                <Target size={14} className="text-[#9aa0a6] shrink-0" />
                                                <span className="truncate">{nodeName as string}</span>
                                            </div>
                                        </td>
                                        
                                        <td className="p-4 text-[#9aa0a6] font-mono text-sm">
                                            <div className="flex items-center gap-2">
                                                <Clock size={14}/> {uptimeSecs}s
                                            </div>
                                        </td>
                                        
                                        <td className="p-4">
                                            <div className="flex flex-col gap-2.5">
                                                {/* LABELS CỦA TOKEN */}
                                                {token.labels && token.labels.length > 0 && (
                                                    <div className="flex flex-wrap items-center gap-2">
                                                        <Tag size={12} className="text-[#fcd663] shrink-0" />
                                                        {token.labels.map((label, idx) => (
                                                            <span key={idx} className="px-2 py-0.5 bg-[#fcd663]/10 text-[#fcd663] border border-[#fcd663]/30 rounded text-xs font-bold font-mono tracking-wider">
                                                                {label}
                                                            </span>
                                                        ))}
                                                    </div>
                                                )}

                                                <div className="flex items-center gap-2 text-xs text-[#9aa0a6] font-mono">
                                                    <MapPin size={12} className="text-[#8ab4f8]"/>
                                                    Steps: {token.history?.length || 0} 
                                                    <span className="truncate opacity-50 ml-1" title={token.history?.join(' -> ')}>
                                                        ({token.history?.slice(-3).map(uid => nodesMap[uid]?.type).join('→')}...)
                                                    </span>
                                                </div>
                                                
                                            </div>
                                        </td>
                                    </tr>
                                );
                            })
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};