import { create } from "zustand";
import {
  Node,
  Edge,
} from "@xyflow/react";

import { applyNodeChanges, applyEdgeChanges, NodeChange, EdgeChange, Connection, addEdge } from "@xyflow/react";
import { TagValue } from "./GlobalTagsStore";
import { NodeAPI } from "../../api/nodeApi";
import { SequencerEngine, SequencerCompiler } from "./SequencerEngine";

/* =========================
   TYPES
========================= */

export type OperandType =
  | "+"
  | "-"
  | "*"
  | "/"
  | ">"
  | ">="
  | "=="
  | "<="
  | "<";

export type SequencerNodeType =
  | "start" | "end" | "proc" | "split" | "join" | "switch" | "comp"
  | "and" | "or" | "delay" | "tov" | "tot" 
  | "exjson" | "buildjson"
  | "portal_in" | "portal_out" | "script" | "writedb";

/* =========================
   CONFIG INTERFACES
========================= */

export interface NodeStartConfig {
  next_node_id: string;
  on_begin_map: Record<string, TagValue>;
}

export interface NodeEndConfig {
  on_end_map: Record<string, TagValue>;
}

export interface NodeProcessConfig {
  next_node_id: string;
  node_title: string;
  logic_object_info : NodeProcessServerData;
  payload_formation_map: Record<string, string | { type: 'tag' | 'const', value: any }>;
  response_receive_map: Record<string, string>;  //json path : write to tag
}

export interface NodeSplitConfig {
  next_nodes_id_list: string[];
}

export interface NodeJoinConfig {
  next_node_id: string;
  required_tokens_count: number;
}

export interface NodeSwitchConfig {
  next_node_id_map: Record<string, string>; //value_to_compare : next_node_id
  tag_id: string;
}

export interface NodeComputeConfig {
  next_node_id: string;
  tag_id_a: string;
  tag_id_b: string;
  operand: OperandType;
  target_tag_id: string;
}

export interface NodeAndConfig {
  next_node_id: string;
  tag_id_a: string;
  tag_id_b: string;
}

export interface NodeOrConfig {
  next_node_id: string;
  tag_id_a: string;
  tag_id_b: string;
}

export interface NodeDelayConfig {
  next_node_id: string;
  delay_duration: number; // Mặc định là số
  is_dynamic?: boolean;   // Cờ đánh dấu dùng Tag
  delay_tag_id?: string;  // ID của Tag nếu is_dynamic = true
}

export interface NodeTagOvwrByValConfig {
  next_node_id: string;
  target_tag_id: string;
  ovwr_value: any;
}

export interface NodeTagOvwrByTagConfig {
  next_node_id: string;
  source_tag_id: string;
  target_tag_id: string;
}

export interface NodeExtractJSONConfig {
  next_node_id: string;
  source_tag_id: string;
  aliases: Record<string, string>;
  script: string;
}

export interface NodePortalInConfig {
  next_node_id: string;
  channel_name: string;
}

export interface NodePortalOutConfig {
  next_node_id: string;
  channel_name: string;
}

export interface NodeBuildJSONConfig {
  next_node_id: string;
  target_tag_id: string;
  aliases: Record<string, string>;
  script: string;
}

export interface NodeScriptConfig {
  next_node_id: string;
  input_aliases: Record<string, string>; // VD: { "boxes": "tag_xyxy" } -> JS: IN.boxes
  output_aliases: Record<string, string>; // VD: { "total": "tag_qty" } -> JS: OUT.total
  script_content: string;
}

export interface NodeWriteDBConfig {
  next_node_id: string;
  worker_id: string;
  table_name: string;
  mapping: Record<string, string>; // { "column_name": "tag_id" }
  image_columns: Record<string, boolean>; // { "column_name": true/false }
}

export type SequencerNodeConfig =
  | NodeStartConfig
  | NodeEndConfig
  | NodeProcessConfig
  | NodeSplitConfig
  | NodeJoinConfig
  | NodeSwitchConfig
  | NodeComputeConfig
  | NodeAndConfig
  | NodeOrConfig
  | NodeDelayConfig
  | NodeTagOvwrByValConfig
  | NodeTagOvwrByTagConfig
  | NodeExtractJSONConfig
  | NodeBuildJSONConfig
  | NodeScriptConfig
  | NodePortalInConfig
  | NodePortalOutConfig
  | NodeWriteDBConfig;
  

/* =========================
   NODE DATA
========================= */

export interface NodeProcessServerData{
    worker_id: string,
    logic_object_id: string,
}

export interface SequencerNodeData {
  name?: string;
  type: SequencerNodeType;
  config: SequencerNodeConfig;
  ishighlighted: boolean;
}

export interface TokenValue {
    node_uuid: string;
    status: 'READY' | 'PROCESSING' | 'WAITING' | 'HIJACKED';
    x: number;
    y: number;
    color: string;
    
    // --- NGỮ CẢNH ĐIỀU HƯỚNG ---
    history: string[];       // Nhật ký hành trình (Cực kỳ quan trọng)
    spawnedAt: number;       // Thời gian sống
    labels: string[];        // Các nhãn dán được thu thập trên đường đi (Dynamic Labels)
}


/* =========================
   STORE
========================= */

export interface SequencerState {
  nodes: Node[]; //render nodes, dùng compile graph
  edges: Edge[]; //render nodes, dùng compile graph

  nodes_lookup_map: Record<string, Node>; //for performance look up, để cập nhật UI biểu diễn token trên graph khi chạy runtime
  run_time_token_list: Record<string, TokenValue>; //lưu trữ thông tin token để engine dùng và cho cập nhật UI biểu diễn token khi chạy runtime

  isTokenBlackboardOpen: boolean; 
  toggleTokenBlackboard: () => void;

  isSequencerErrorModalOpen: boolean; // báo lỗi
  SequencerErrorMessage: string; // báo lỗi

  engine_tick_ms: number; //làm một trường để cài đặt tần số quét của sequencer khi chạy

  isCompiling: boolean; // dùng để đặt trạng thái hệ thống và hiển thị nút ấn

  isEngineRunning : boolean; // dùng để đặt trạng thái hệ thống và hiển thị nút ấn

  isGraphDirty : boolean; // dùng để đặt trạng thái hệ thống và hiển thị nút ấn
  
  compiler_log_messages : string[]; // dùng để báo cáo thông tin compiling và lưu lỗi thời gian thực

  usedLogicObjectsIDMap: Record<string, NodeProcessServerData>[]; // node Id : Logic Object ID

  isEditPropertyPanelOpen : boolean; // Dùng để mở bảng panel properties cài đặt cho node Process
  isOnStartEndPropertyPanelOpen : boolean; // dùng để mở bảng panel properties cài đặt cho node Start/ end
  
  setFieldValue: (node_id : string, field: string, value: any) => void; // Helper dùng đặt lại giá trị của một field dữ liệu bất kỳ trong một node (khi đang tạo graph)
  createDefaultConfig: (type: SequencerNodeType) => SequencerNodeData; //Helper dùng tạo node
  addNode: (type: SequencerNodeType,position?: { x: number; y: number }) => void; //Helper dùng tạo node
  updateNodeData: (nodeId : string, newData : any) => void;
  onSelectWorker: (worker_id: string) => Promise<string[]>; // API helper dùng để hiện dữ liệu khi chọn vào worker tương ứng ở trong Process Node properties
  onSelectLogicObject: (worker_id: string, logic_object_id: string) => Promise<Record<string, any>> // API helper dùng để hiện dữ liệu schema đầu vào / ra của một logic object khi ở trong process node properties
  appendCompilerLog: (msg: string) => void; //Thêm thông tin vào log 
  compileGraph: () => Promise<void>; //Compile graph thành hệ thống sẵn sàng chạy được cho engine.
  runEngine: () => void; //Bắt đầu chạy hệ thống
  stopEngine: () => void; //Dừng hệ thống
  cleanUpCompilerLog: () => void; //Xóa log hệ thống (có thể làm một nút để dọn dẹp cho đỡ rác mắt nếu cần)
  onNodesChange: (changes: NodeChange[]) => void;
  onEdgesChange: (changes: EdgeChange[]) => void;
  onConnect: (connection: Connection) => void;
  markGraphDirty: () => void;

  past: { nodes: Node[]; edges: Edge[] }[];
  future: { nodes: Node[]; edges: Edge[] }[];
  clipboard: { nodes: Node[] } | null;
  takeSnapshot: () => void;
  undo: () => void;
  redo: () => void;
  copySelection: () => void;
  pasteSelection: (mousePos?: { x: number; y: number }) => void;
}

/* =========================
   STORE
========================= */
// TODO: REMEMBER TO PERSIST
export const useSequencerStore =
  create<SequencerState>((set, get) => ({
    nodes: [],
    edges: [],

    nodes_lookup_map: {},
    run_time_token_list: {},

    isTokenBlackboardOpen: false,
    toggleTokenBlackboard: () => set((state) => ({ isTokenBlackboardOpen: !state.isTokenBlackboardOpen })),

    isSequencerErrorModalOpen: false,
    SequencerErrorMessage: "",
    
    engine_tick_ms : 25, //25ms = 10fps

    isCompiling: false,

    isEngineRunning: false,

    isGraphDirty: true,

    compiler_log_messages: [],

    usedLogicObjectsIDMap: [],

    isEditPropertyPanelOpen: false,
    isOnStartEndPropertyPanelOpen: false,

    /* =========================
       DEFAULT CONFIG FACTORY
    ========================= */

    setFieldValue: (node_id, field, value) => {
        get().markGraphDirty();
        set((state) => ({
            nodes: state.nodes.map((node) =>
            node.id !== node_id
                ? node
                : {
                    ...node,
                    data: {
                    ...node.data,
                    sequencer_data: {
                        ...node.data.sequencer_data as any,
                        config: {
                        ...(node.data.sequencer_data as any)?.config || {},
                        [field]: value,
                        },
                    },
                    },
                }
            ),
        }));
    },

    createDefaultConfig: (type: SequencerNodeType): SequencerNodeData => {
      switch (type) {
        case "start":
          return {
            type,
            config: {
              next_node_id: "",
              on_begin_map: {},
            },
            ishighlighted : false
          };

        case "end":
          return {
            type,
            config: {
              on_end_map: {},
            },
            ishighlighted : false
          };

        case "proc":
          return {
            type,
            config: {
              next_node_id: "",
              node_title: "Process",
              logic_object_info : {worker_id: "", logic_object_id: ""},
              payload_formation_map: {},
              response_receive_map: {},
            },
            ishighlighted : false
          };

        case "split":
          return {
            type,
            config: {
              next_nodes_id_list: [],
            },
            ishighlighted : false
          };

        case "join":
          return {
            type,
            config: {
              next_node_id: "",
              required_tokens_count: 1,
            },
            ishighlighted : false
          };

        case "switch":
          return {
            type,
            config: {
              next_node_id_map: {},
              tag_id: "",
            },
            ishighlighted : false
          };

        case "comp":
          return {
            type,
            config: {
              next_node_id: "",
              tag_id_a: "",
              tag_id_b: "",
              operand: "+",
              target_tag_id: "",
            },
            ishighlighted : false
          };

        case "and":
          return {
            type,
            config: {
              next_node_id: "",
              tag_id_a: "",
              tag_id_b: "",
            },
            ishighlighted : false
          };

        case "or":
          return {
            type,
            config: {
              next_node_id: "",
              tag_id_a: "",
              tag_id_b: "",
            },
            ishighlighted : false
          };

        case "delay":
          return {
            type,
            config: {
              next_node_id: "",
              delay_duration: 1,
            },
            ishighlighted : false
          };

        case "tov":
          return {
            type,
            config: {
              next_node_id: "",
              target_tag_id: "",
              ovwr_value: null,
            },
            ishighlighted : false
          };

        case "tot":
          return {
            type,
            config: {
              next_node_id: "",
              source_tag_id: "",
              target_tag_id: "",
            },
            ishighlighted : false
          };

        case "exjson":
          return {
            type,
            config: {
              next_node_id: "",
              source_tag_id: "",
              aliases: {},
              script: "{\n  \n}",
            },
            ishighlighted: false
          };

        case "buildjson":
          return {
            type,
            config: {
              next_node_id: "",
              target_tag_id: "",
              aliases: {},
              script: "{\n  \n}",
            },
            ishighlighted: false
          };

        case "script":
          return {
            type,
            config: {
              next_node_id: "",
              input_aliases: {},
              output_aliases: {},
              script_content: "// Write your JS logic here...\n// Ex 1: let len = IN.arr ? IN.arr.length : 0;\n// OUT.result = len * 2;\n\n// Ex 2: let box = UI.get(\"BBox 1\");\n// if (box) UI.set(\"BBox 1\", { w: box.w + 10, style: { fillColor: '#ff0000' } });\n",
            },
            ishighlighted: false,
            name: "JS SCRIPT"
          };

        case "portal_in":
          return {
            type,
            config: { next_node_id: "", channel_name: "Channel_1" },
            ishighlighted: false
          };

        case "portal_out":
          return {
            type,
            config: { next_node_id: "", channel_name: "Channel_1" },
            ishighlighted: false
          };

        case "writedb":
          return {
            type,
            config: { next_node_id: "", worker_id: "", table_name: "", mapping: {}, image_columns: {} },
            ishighlighted: false
          };
      }
    },

    /* =========================
       ADD NODE
    ========================= */

    addNode: (type: SequencerNodeType,position = { x: 100, y: 100 }) => {
      const id = `${type}_${Date.now()}`;

      const seqData =
        get().createDefaultConfig(type);

      const newNode: Node = {
        id,
        type, // phải match nodeTypes của ReactFlow
        position,

        data: {
          sequencer_data: seqData
        },
      };

      set((state) => ({
        nodes: [...state.nodes, newNode],
      }));
    },

    updateNodeData: (nodeId, newData) => {
      set((state) => ({
        nodes: state.nodes.map((node) =>
          node.id === nodeId 
            ? { ...node, data: { ...node.data, ...newData } } 
            : node
        ),
      }));
    },

    onSelectWorker : async (worker_id) => {
      // Process Node Properties Panel will use this result to know how to render its Logic Objects Slection field.
      const isMaster = worker_id === "master_gateway";
      try{
          const resp = await (
            isMaster
              ? NodeAPI.master_get_logic_id_list()
              : NodeAPI.proxy_get_logic_id_list(worker_id)
          );
          return resp;
      } catch (error: any){
        set({isSequencerErrorModalOpen: true, SequencerErrorMessage: `Error trying to get logic objects ids list: ${error?.detail}`})
      }
    },

    onSelectLogicObject : async (worker_id, logic_object_id) => {
      // Process Node Properties Panel will use this result to know how to render its fields
        const isMaster = worker_id === "master_gateway";
        try{
          const resp = await (
            isMaster
              ? NodeAPI.master_get_inout_schemas(logic_object_id)
              : NodeAPI.proxy_get_inout_schemas(worker_id, logic_object_id)
          )
          console.log(resp)
          return resp;
        } catch (error: any){
          set({isSequencerErrorModalOpen: true, SequencerErrorMessage: `Error trying to get logic objects ids list: ${error?.detail}`})
        }
    },
    appendCompilerLog: (msg) => {
      set((state) => ({
        compiler_log_messages: [...state.compiler_log_messages, msg]
      }))
    },

    compileGraph : async () => {
      set({isEngineRunning: false});
      set({isCompiling : true});
      const compiled_success = await SequencerCompiler.compile(get().nodes, get().edges);
      if (compiled_success){
        set({isGraphDirty: false});

        //Create look up map for O(1) performance (this is used for doing the run time highlighting node effect of the Sequencer Graph)
        for(const node of get().nodes){
          get().nodes_lookup_map[node.id] = node;
        }
      }
      set({isCompiling : false});
    },

    runEngine : () => {
      if(get().isGraphDirty) {
        get().appendCompilerLog("Sequencer Graph is dirty, please recompile!")
        return;
      }
      set({isEngineRunning : true})
      const engine = SequencerEngine.getInstance();
      engine.startEngine();
      engine.tick()
    },

    stopEngine : () => {
      set({run_time_token_list: {}})
      set({isEngineRunning: false})
      SequencerEngine.getInstance().stopEngine();
    },

    cleanUpCompilerLog:() => {
      set({compiler_log_messages : []});
    },

    markGraphDirty: () => set({ isGraphDirty: true }),

    onNodesChange: (changes) => {
      set({
        nodes: applyNodeChanges(changes, get().nodes),
      });
      // Nếu có sự thay đổi tọa độ hoặc xóa, đánh dấu dirty
      if (changes.some(c => c.type === 'position' || c.type === 'remove' || c.type === 'add')) {
          get().markGraphDirty();
      }
    },

    onEdgesChange: (changes) => {
      set({
        edges: applyEdgeChanges(changes, get().edges),
      });
      get().markGraphDirty();
    },

    onConnect: (connection) => {
      set({
        edges: addEdge(connection, get().edges),
      });
      get().markGraphDirty();
    },
    past: [],
  future: [],
  clipboard: null,

  takeSnapshot: () => {
    const { nodes, edges, past } = get();
    // Deep Clone trạng thái hiện tại và lưu tối đa 50 bước
    const newPast = [
      ...past,
      {
        nodes: JSON.parse(JSON.stringify(nodes)),
        edges: JSON.parse(JSON.stringify(edges)),
      },
    ].slice(-50);
    set({ past: newPast, future: [] });
  },

  undo: () => {
    const { past, future, nodes, edges } = get();
    if (past.length === 0) return;

    const previousState = past[past.length - 1];
    const newPast = past.slice(0, past.length - 1);

    set({
      past: newPast,
      future: [{ nodes: JSON.parse(JSON.stringify(nodes)), edges: JSON.parse(JSON.stringify(edges)) }, ...future],
      nodes: previousState.nodes,
      edges: previousState.edges,
      isGraphDirty: true, // Đánh dấu cần compile lại
    });
  },

  redo: () => {
    const { past, future, nodes, edges } = get();
    if (future.length === 0) return;

    const nextState = future[0];
    const newFuture = future.slice(1);

    set({
      past: [...past, { nodes: JSON.parse(JSON.stringify(nodes)), edges: JSON.parse(JSON.stringify(edges)) }],
      future: newFuture,
      nodes: nextState.nodes,
      edges: nextState.edges,
      isGraphDirty: true,
    });
  },

  copySelection: () => {
    const { nodes } = get();
    const selectedNodes = nodes.filter((n) => n.selected);
    // CHẶN SINGLETONS: Không copy khối start và end
    const copyableNodes = selectedNodes.filter(n => n.type !== 'start' && n.type !== 'end');

    if (copyableNodes.length === 0) return;
    set({ clipboard: { nodes: copyableNodes } });
  },

  pasteSelection: (mousePos) => {
    const { clipboard, nodes, edges, takeSnapshot } = get();
    if (!clipboard || clipboard.nodes.length === 0) return;

    takeSnapshot();

    // Thuật toán tìm tọa độ gốc cụm node đang copy
    const minX = Math.min(...clipboard.nodes.map((n) => n.position.x));
    const minY = Math.min(...clipboard.nodes.map((n) => n.position.y));

    const deltaX = mousePos ? mousePos.x - minX : 50;
    const deltaY = mousePos ? mousePos.y - minY : 50;

    const pastedNodes = clipboard.nodes.map((node) => {
      // Sinh ID mới dựa trên type của node sequencer
      const newId = `${node.type}_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`;
      const newData = JSON.parse(JSON.stringify(node.data));

      return {
        ...node,
        id: newId,
        selected: true,
        position: {
          x: node.position.x + deltaX,
          y: node.position.y + deltaY,
        },
        data: newData,
      };
    });

    const unselectedOldNodes = nodes.map((n) => ({ ...n, selected: false }));
    const unselectedOldEdges = edges.map((e) => ({ ...e, selected: false }));

    set({
      nodes: [...unselectedOldNodes, ...pastedNodes],
      edges: unselectedOldEdges,
      isGraphDirty: true,
    });
  },
  }));