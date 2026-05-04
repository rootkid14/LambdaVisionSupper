// src/UI_Engine/Hooks/useKeyboardTrigger.ts
import { useEffect } from 'react';
import { useKeyboardTriggerStore } from '../UIEngineStores/KeyboardTriggerStore';
import { useTagDb } from '../UIEngineStores/GlobalTagsStore';
import { useSequencerStore } from '../UIEngineStores/SequencerStores'; // <-- IMPORT MỚI

export const useKeyboardTrigger = () => {
    const shortcuts = useKeyboardTriggerStore(state => state.shortcuts);
    const { writeTag, readTag } = useTagDb.getState();
    const isEngineRunning = useSequencerStore(state => state.isEngineRunning); // Lắng nghe state của Engine

    useEffect(() => {
        // --- CẢI TIẾN QUAN TRỌNG: NẾU ENGINE CHƯA CHẠY, NGẮT LUÔN VIỆC LẮNG NGHE ---
        if (!isEngineRunning) return;

        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
            if (e.repeat) return;

            shortcuts.forEach(shortcut => {
                if (shortcut.keyCode === e.code && shortcut.targetTag) {
                    e.preventDefault();
                    switch (shortcut.actionType) {
                        case 'toggle': writeTag(shortcut.targetTag, !readTag(shortcut.targetTag)); break;
                        case 'setToTrue': writeTag(shortcut.targetTag, true); break;
                        case 'setToFalse': writeTag(shortcut.targetTag, false); break;
                        case 'pulse': writeTag(shortcut.targetTag, true); break;
                    }
                }
            });
        };

        const handleKeyUp = (e: KeyboardEvent) => {
            if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
            shortcuts.forEach(shortcut => {
                if (shortcut.keyCode === e.code && shortcut.targetTag && shortcut.actionType === 'pulse') {
                    writeTag(shortcut.targetTag, false);
                }
            });
        };

        window.addEventListener('keydown', handleKeyDown);
        window.addEventListener('keyup', handleKeyUp);

        return () => {
            window.removeEventListener('keydown', handleKeyDown);
            window.removeEventListener('keyup', handleKeyUp);
        };
    }, [shortcuts, isEngineRunning]); // Trigger re-render hook khi Engine đổi trạng thái
};