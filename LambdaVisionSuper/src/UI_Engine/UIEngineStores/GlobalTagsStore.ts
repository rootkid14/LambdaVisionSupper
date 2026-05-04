import { create } from "zustand";
import { persist, createJSONStorage, StateStorage } from "zustand/middleware";
import { get, set, del } from 'idb-keyval';

const idbStorage: StateStorage = {
    getItem: async (name: string) => (await get(name)) || null,
    setItem: async (name: string, value: string) => await set(name, value),
    removeItem: async (name: string) => await del(name),
};

export type TagValue = string | number | boolean | null | Record<string, any> | any[] | Blob | File;

export const inferTagType = (value: any): string => { // Trong PropertiesSidebar thì tên là inferType nhé
    if (value === null || value === undefined) return 'any';
    if (typeof value === 'boolean') return 'boolean';
    if (typeof value === 'number') return 'number';
    
    // Nhận diện mảng và JSON
    if (Array.isArray(value)) return 'list'; 
    if (typeof value === 'object') return 'dict'; 
    
    if (typeof value === 'string') {
        // Gom chung Ảnh Base64 và Raw Base64 vào 1 kiểu duy nhất là 'base64'
        if (value.startsWith('data:image/')) return 'base64';
        if (value.length > 200 && !value.includes(' ') && /^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(value)) {
            return 'base64';
        }
        return 'string';
    }
    return 'any';
};


interface TagDBStore {
    tags: Record<string, TagValue>;

    isGlobalTagsTableOpen: boolean;

    writeTag: (key: string, value: TagValue) => void;
    writeTagsBatch: (tagsToUpdate: Record<string, TagValue>) => void;
    readTag: (key: string) => TagValue | undefined;
    getAllTags: () => Record<string, TagValue>;
    deleteTag: (key: string) => void;
}

export const useTagDb = create<TagDBStore>()(
    persist(
        (set, get) => ({
            tags: {},
            isGlobalTagsTableOpen: false,

            writeTag: (key, value) => set((state) => ({
                tags: { ...state.tags, [key]: value }
            })),

            writeTagsBatch: (tagsToUpdate) => set((state) => ({
                tags: { ...state.tags, ...tagsToUpdate }
            })),

            readTag: (key) => get().tags[key],
            getAllTags: () => get().tags,
            deleteTag: (key) => set((state) => {
                const newTags = { ...state.tags };
                delete newTags[key];
                return { tags: newTags };
            })
        }),
        {
            name: "tag-db-storage",
            storage: createJSONStorage(() => idbStorage),
        }
    )
);