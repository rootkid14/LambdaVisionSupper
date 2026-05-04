import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

export type TriggerActionType = 'toggle' | 'setToTrue' | 'setToFalse' | 'pulse';

export interface Shortcut {
    id: string;
    keyLabel: string; // VD: 'SPACE', 'A', 'ENTER' (để hiển thị)
    keyCode: string;  // VD: 'Space', 'KeyA', 'Enter' (để hệ thống bắt chính xác)
    targetTag: string;
    actionType: TriggerActionType;
}

export interface KeyboardTriggerStore {
    isSettingsModalOpen: boolean;
    shortcuts: Shortcut[];

    // Actions
    toggleSettingsModal: () => void;
    addShortcut: () => void;
    updateShortcut: (id: string, updates: Partial<Shortcut>) => void;
    removeShortcut: (id: string) => void;
}

export const useKeyboardTriggerStore = create<KeyboardTriggerStore>()(
    persist(
        (set) => ({
            isSettingsModalOpen: false,
            shortcuts: [],

            toggleSettingsModal: () => set((state) => ({ 
                isSettingsModalOpen: !state.isSettingsModalOpen 
            })),

            addShortcut: () => set((state) => ({
                shortcuts: [
                    ...state.shortcuts, 
                    {
                        id: `shortcut_${Date.now()}`,
                        keyLabel: 'UNASSIGNED',
                        keyCode: '',
                        targetTag: '',
                        actionType: 'toggle'
                    }
                ]
            })),

            updateShortcut: (id, updates) => set((state) => ({
                shortcuts: state.shortcuts.map(s => s.id === id ? { ...s, ...updates } : s)
            })),

            removeShortcut: (id) => set((state) => ({
                shortcuts: state.shortcuts.filter(s => s.id !== id)
            }))
        }),
        {
            name: "keyboard-trigger-storage",
            storage: createJSONStorage(() => localStorage),
            // Không lưu trạng thái đóng/mở của modal khi F5
            partialize: (state) => ({ shortcuts: state.shortcuts }),
        }
    )
);