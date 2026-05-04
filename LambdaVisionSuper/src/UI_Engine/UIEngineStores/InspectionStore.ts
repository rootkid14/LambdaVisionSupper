import { create } from "zustand";
import { useTagDb } from './GlobalTagsStore';
import { COLOR_PALETTE } from "../../utils/ColorConst";

export type DrawType = 'screen' | 'thumbnail' | 'frame' | 'bounding_box' | 'text' | 'line' | 'bounding_circle';


export interface DataBinding {
    propName: string;
    globalTagKey: string;
}

export interface BaseUINode{
    id: string;
    name: string;
    type: DrawType;
}

export interface Screen extends BaseUINode{
    id: string;
    type: DrawType;
    children_id: string[];
    size_x : number;
    size_y : number;
    style: {
        fillColor: string; 
    };
    bindings: DataBinding[];
}

export interface Thumbnail extends BaseUINode{
    id: string;
    type: DrawType;
    screen_id: string;
}

export interface Frame extends BaseUINode{
    id: string;
    type: DrawType;
    parent_id: string;
    children_id : string[];
    x : number;
    y : number;
    size_x : number;
    size_y : number;
    rotation: number;
    style: {
        strokeColor: string;
        border_thickness: number;
        fillColor: string;
        default_image: any;
        bgImage: any;
    }
    bindings: DataBinding[];
    isVisible: boolean;
}

export interface BoundingBoxNode extends BaseUINode{
    id: string;
    type: DrawType;
    parent_id: string;
    z_order : number;
    x: number;
    y: number;
    size_x : number;
    size_y : number;
    rotation: number;
    style: {
        strokeColor: string;
        border_thickness: number;
        dash?: number[]
    }
    bindings: DataBinding[];
    isVisible: boolean;
}

export interface TextNode extends BaseUINode{
    id: string;
    type: DrawType;
    parent_id: string;
    z_order: number
    content: string;
    x: number;
    y: number;
    size_x: number;
    size_y: number;
    rotation: number;
    style: {
        fontSize: number;
        fontColor: string;
        fontFamily: string;
        fillcolor: string;
        align: 'left' | 'center' | 'right';
    };
    binding: DataBinding[];
    isVisible: boolean;
}

export interface BoundingCircleNode extends BaseUINode{
    id: string;
    type: DrawType;
    parent_id: string;
    z_order : number;
    x: number;
    y: number;
    radius : number;
    style: {
        strokeColor: string;
        border_thickness: number;
        dash?: number;
    }
    bindings: DataBinding[];
    isVisible: boolean;
}

export interface LineNode extends BaseUINode{
    id: string;
    type: DrawType;
    parent_id: string;
    z_order : number;
    x1: number;
    x2: number;
    y1 : number;
    y2 : number;
    style: {
        strokeColor: string;
        thickness: number;
        dash?: number;
    }
    bindings: DataBinding[];
    isVisible: boolean;
}

export interface ActionMenuContext {
    isOpen: boolean;
    x: number;
    y: number;
    target_id: string;
    target_type: DrawType;
}

export interface PropertiesPanelContext {
    isOpen: boolean;
    target_id: string | null;
}

export interface NameLabelConfig {
    isVisible: boolean;
    fontSize: number;
    fontColor: string;
    fontFamily: string;
}


export interface UIEngineStore {
    components_map: Record<string, any>;
    selectedNodeIds: string[];
    showDataTable: boolean;
    nameLabelConfig: NameLabelConfig;
    showTerminalLog: boolean;
    activeScreenId: string | null;

    importFileContext: File | null;
    setImportFile: (file: File | null) => void;

    viewportMode: 'normal' | 'fullViewPort' | 'fullScreen';

    actionMenu: ActionMenuContext;
    propertyPanel: PropertiesPanelContext;
    renameModal: { isOpen: boolean; target_id: string; currentName: string };

    // Actions
    updateComponentProps: (id: string, new_props: any) => void;
    renameComponent: (id: string, newName: string) => void;
    addComponent: (type: DrawType, parent_id: string, initial_x: number, initial_y: number) => void;
    addScreen: () => void;
    deleteComponents: (ids: string[]) => void;
    selectComponents: (ids: string[]) => void;
    changeScreen: (screen_id: string) => void;
    setViewportMode: (mode: 'normal' | 'fullViewPort' | 'fullScreen') => void;
    
    // UI Toggles & Menus
    openActionMenu: (target_id: string, target_type: DrawType, client_x: number, client_y: number, local_x: number, local_y: number) => void;
    closeActionMenu: () => void;
    openPropertiesPanel: (target_id: string) => void;
    closePropertiesPanel: () => void;
    openRenameModal: (id: string, name: string) => void;
    closeRenameModal: () => void;
    toggleTerminalLog: () => void;
    updateNameLabelConfig: (newConfig: Partial<NameLabelConfig>) => void;

    // Binding
    bindTagToProperty: (nodeId: string, propName: string, globalTagKey: string) => void;
    unbindTag: (nodeId: string, propName: string) => void;
}

export const useUIEngine = create<UIEngineStore>((set, get) => ({
    components_map: {
        // Screen Mặc định
        'screen_1': { 
            id: 'screen_1', 
            type: 'screen', 
            name: 'Main Screen', 
            // KHAI BÁO ID CỦA FRAME CON ĐỂ SCREEN RENDER NÓ
            children_id: ['frame_intro'], 
            size_x: 1920, 
            size_y: 1080, 
            style: { fillColor: '#696969' }, 
            bindings: [] 
        },
        
        // --- FRAME HƯỚNG DẪN MẶC ĐỊNH ---
        'frame_intro': {
            id: 'frame_intro',
            type: 'frame',
            name: 'Welcome Frame',
            parent_id: 'screen_1',
            // KHAI BÁO ID CỦA TEXT CON ĐỂ FRAME RENDER NÓ
            children_id: ['text_intro'], 
            x: 100, // Cách mép trái màn hình 100px
            y: 100, // Cách mép trên màn hình 100px
            size_x: 600,
            size_y: 400,
            rotation: 0,
            style: { 
                strokeColor: '#8ab4f8', 
                border_thickness: 2, 
                fillColor: 'rgba(138, 180, 248, 0.1)' 
            },
            bindings: [],
            isVisible: true
        },

        // --- TEXT HƯỚNG DẪN BÊN TRONG FRAME ---
        'text_intro': {
            id: 'text_intro',
            type: 'text',
            name: 'Guide Text',
            parent_id: 'frame_intro',
            content: "WELCOME TO LAMBDAVISION SUPER\n\n[ Hướng dẫn sử dụng nhanh ]\n\n1. Chuột phải vào nền trống để thêm Frame.\n2. Chuột phải vào Frame để thêm các UI (Box, Circle, Text).\n3. Mở Action Menu > Properties để thiết lập Data Bindings.\n4. Ấn nút Settings ở thanh Toolbar để cài phím tắt.\n5. Cuộn chuột để Zoom, kéo nền để Pan, chuột phải > Full Viewport.\n\nChúc bạn có một trải nghiệm hệ thống tuyệt vời!",
            x: 40, 
            y: 40, 
            size_x: 520,
            size_y: 320,
            rotation: 0,
            style: { 
                fontSize: 18, 
                fontColor: '#e8eaed', 
                fontFamily: 'monospace' 
            },
            bindings: [],
            isVisible: true
        }
    },
    selectedNodeIds: [], showDataTable: false, showNames: true, showTerminalLog: false, activeScreenId: 'screen_1',
    actionMenu: { isOpen: false, x: 0, y: 0, target_id: '', target_type: 'screen' } as any,
    propertyPanel: { isOpen: false, target_id: null },
    renameModal: { isOpen: false, target_id: '', currentName: '' },
    nameLabelConfig: {
        isVisible: true,
        fontSize: 20,
        fontColor: '#8ab4f8',
        fontFamily: 'Arial'
    },

    viewportMode: 'normal',
    importFileContext: null,

    updateComponentProps: (id, new_props) => set((state) => {
        const node = state.components_map[id];
        if (!node) return state;
        return { components_map: { ...state.components_map, [id]: { ...node, ...new_props } } };
    }),

    renameComponent: (id, newName) => set((state) => {
        const node = state.components_map[id];
        if (!node) return state;
        return { components_map: { ...state.components_map, [id]: { ...node, name: newName } } };
    }),

    addScreen: () => set((state) => {
        const newId = `screen_${Date.now()}`;
        const count = Object.values(state.components_map).filter(n => n.type === 'screen').length + 1;
        return {
            components_map: { 
                ...state.components_map, 
                [newId]: { 
                    id: newId, 
                    type: 'screen', 
                    name: `Screen ${count}`, 
                    children_id: [], 
                    size_x: 1920, 
                    size_y: 1080, 
                    // Thêm style khi đẻ Screen mới
                    style: { fillColor: '#202124' }, 
                    bindings: [] 
                } 
            },
            activeScreenId: newId
        };
    }),

    addComponent: (type, parent_id, initial_x, initial_y) => set((state) => {
        const newId = `${type}_${Date.now()}`;
        const parent = state.components_map[parent_id];
        if(!parent) return state;

        // Thuật toán: Thêm vào Frame -> Auto Center & Resize an toàn
        let finalX = initial_x; let finalY = initial_y;
        let finalW = 100; let finalH = 100; let finalR = 50;

        if (parent.type === 'frame' && type !== 'frame') {
            finalW = Math.min(100, parent.size_x * 0.8); // Không được to quá 80% Frame
            finalH = Math.min(100, parent.size_y * 0.8);
            finalR = Math.min(50, parent.size_x * 0.4, parent.size_y * 0.4);
            
            // Căn chính giữa Frame
            finalX = type === 'bounding_circle' ? parent.size_x / 2 : (parent.size_x - finalW) / 2;
            finalY = type === 'bounding_circle' ? parent.size_y / 2 : (parent.size_y - finalH) / 2;
        }

        const newNode: any = { id: newId, type, name: `${type} ${Math.floor(Math.random() * 100)}`, parent_id, x: finalX, y: finalY, rotation: 0, bindings: [], isVisible: true };

        if (type === 'frame') { newNode.size_x = 400; newNode.size_y = 300; newNode.children_id = []; newNode.style = { strokeColor: '#8ab4f8', border_thickness: 2, fillColor: 'rgba(138, 180, 248, 0.1)' }; }
        if (type === 'bounding_box') { newNode.size_x = finalW; newNode.size_y = finalH; newNode.style = { strokeColor: '#f28b82', border_thickness: 2 }; }
        if (type === 'bounding_circle') { newNode.radius = finalR; newNode.style = { strokeColor: '#fcd663', border_thickness: 2 }; }
        if (type === 'text') { newNode.size_x = 100; newNode.size_y = 30; newNode.content = 'Double click to edit'; newNode.style = { fontSize: 16, fontColor: '#e8eaed', fontFamily: 'Arial' }; }

        return { components_map: { ...state.components_map, [newId]: newNode, [parent_id]: { ...parent, children_id: [...(parent.children_id || []), newId] } } };
    }),

    deleteComponents: (ids) => set((state) => {
        const newMap = { ...state.components_map };
        let newActiveScreenId = state.activeScreenId;
        ids.forEach(id => {
            const node = newMap[id];
            if (node) {
                if (node.parent_id && newMap[node.parent_id]) { newMap[node.parent_id].children_id = newMap[node.parent_id].children_id.filter((c: string) => c !== id); }
                if (node.type === 'screen' && id === state.activeScreenId) {
                    const remaining = Object.keys(newMap).filter(k => newMap[k].type === 'screen' && k !== id);
                    newActiveScreenId = remaining.length > 0 ? remaining[0] : null;
                }
            }
            delete newMap[id]; 
        });
        return { components_map: newMap, selectedNodeIds: [], actionMenu: { ...state.actionMenu, isOpen: false }, activeScreenId: newActiveScreenId };
    }),

    selectComponents: (ids) => set({ selectedNodeIds: ids }), changeScreen: (id) => set({ activeScreenId: id, selectedNodeIds: [] }),
    setViewportMode: (mode) => set({ viewportMode: mode }),

    openActionMenu: (id, type, cx, cy, lx, ly) => set({ actionMenu: { isOpen: true, x: cx, y: cy, target_id: id, target_type: type, local_x: lx, local_y: ly } as any, selectedNodeIds: type !== 'screen' && type !== 'thumbnail' ? [id] : [] }),
    closeActionMenu: () => set((state) => ({ actionMenu: { ...state.actionMenu, isOpen: false } })),
    
    openPropertiesPanel: (id) => set((state) => ({ 
        propertyPanel: { isOpen: true, target_id: id }, 
        actionMenu: { ...state.actionMenu, isOpen: false } 
    })),
    closePropertiesPanel: () => set({ propertyPanel: { isOpen: false, target_id: null } }),
    
    openRenameModal: (id, name) => set((state) => ({ 
        renameModal: { isOpen: true, target_id: id, currentName: name }, 
        actionMenu: { ...state.actionMenu, isOpen: false } 
    })),
    closeRenameModal: () => set({ renameModal: { isOpen: false, target_id: '', currentName: '' } }),

    toggleTerminalLog: () => set((state) => ({ showTerminalLog: !state.showTerminalLog })),

    updateNameLabelConfig: (newConfig) => set((state) => ({
        nameLabelConfig: { ...state.nameLabelConfig, ...newConfig }
    })),

    bindTagToProperty: (nodeId, propName, tagKey) => set((state) => {
        const node = state.components_map[nodeId];
        return { components_map: { ...state.components_map, [nodeId]: { ...node, bindings: [...node.bindings.filter((b: any) => b.propName !== propName), { propName, globalTagKey: tagKey }] } } };
    }),
    unbindTag: (nodeId, propName) => set((state) => {
        const node = state.components_map[nodeId];
        return { components_map: { ...state.components_map, [nodeId]: { ...node, bindings: node.bindings.filter((b: any) => b.propName !== propName) } } };
    }),

    setImportFile: (file) => set({ importFileContext: file }),
}));

export const useDataBinding = (bindings: DataBinding[] = [], propName: string, localValue: any) => {
    const binding = bindings.find(b => b.propName === propName);
    const globalValue = useTagDb(state => binding ? state.tags[binding.globalTagKey] : undefined);
    
    if (globalValue === undefined || globalValue === null || globalValue === "" || globalValue === "data:image/empty") {
        return localValue;
    }
    
    return globalValue;
};


