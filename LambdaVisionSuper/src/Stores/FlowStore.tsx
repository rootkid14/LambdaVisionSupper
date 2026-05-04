// store/FlowStore.ts
import { create } from "zustand";
import {
  Node,
  Edge,
  OnNodesChange,
  OnEdgesChange,
  OnConnect,
  applyNodeChanges,
  applyEdgeChanges,
  addEdge,
} from "@xyflow/react";

import { WorkerDetails } from "../Stores/FleetDashboardStores";
import { NodeAPI } from "../api/nodeApi";

import {persist, createJSONStorage} from "zustand/middleware"

/* =========================================================
   I. MANIFEST TYPES
========================================================= */

export type NodeKind = "1" | "2" | "3" | "4" | "5";
/*
1 = normal node
2 = inline node
3 = object node
4= FUNCTION
5 = API
*/

export type DataType = 
'boolean' 
| 'number' 
| 'string' 
| 'numpy_array' 
| 'tensor' 
| 'any' 
| "object_ref" 
| "json" 
| "dict" 
| "list"
| "base64"
;

export interface PinManifest {
  id: string;
  label: string;
  dataType: DataType;
}

export interface ConfigFieldManifest {
  name: string;
  label?: string;
  type?: string;
  required?: boolean;
  default?: any;
  placeholder?: string;
  options?: string[];
}

/* ---------- Base ---------- */

export interface BaseManifest {
  type: NodeKind;
  class: string;

  label: string;
  description: string;
  color: string;

  inputs: PinManifest[];
  outputs: PinManifest[];

  config_fields: ConfigFieldManifest[];
}

/* ---------- Inline Node ---------- */

export interface InlineManifest extends BaseManifest {
  inlineInputType: "text" | "number" | "checkbox" | string;
}

/* ---------- Object Node ---------- */

export interface ObjectManifest extends BaseManifest {
  functions: string[];
}

/* ---------- Union ---------- */

export type NodeManifest =
  | BaseManifest
  | InlineManifest
  | ObjectManifest;

/* =========================================================
   II. GRAPH FILE TYPES
========================================================= */

export interface GraphFile {
  nodes: Node[];
  edges: Edge[];
}

export interface GraphValidationResult {
  ok: boolean;
  errors: string[];
}

// For reseting page
const initialState = {
  nodes: [],
  edges: [],

  this_worker_infor: null,

  nodeCatalogueList: [],
  nodeCatalogueMap: {},
  isCatalogueLoaded: false,

  isLoading: false,
  errorMessage: "",
  isErrorModalOpen: false,

  input_simulator_data: {},  
  result_inspector_data: {},
}


//For Preflight run:
export interface PreflightData {
  graph: GraphFile;
  preflight_payload: any;
}

/* =========================================================
   III. STORE STATE
========================================================= */

interface FlowState {
  /* ---------- Graph Runtime ---------- */
  nodes: Node[];
  edges: Edge[];

  /* ---------- Environment ---------- */
  this_worker_infor: WorkerDetails | null;

  /* ---------- Catalogue ---------- */
  nodeCatalogueList: NodeManifest[];
  nodeCatalogueMap: Record<string, NodeManifest>;
  isCatalogueLoaded: boolean;

  /* ---------- UI ---------- */
  isLoading: boolean;
  errorMessage: string;
  isErrorModalOpen: boolean;

  /* For preflight / testing graph */
  input_simulator_data : any | null  //For preview of dummy input data in the debug panel
  result_inspector_data : any | null //For preview of preflight run result received from BE

  /* ---------- React Flow handlers ---------- */
  onNodesChange: OnNodesChange;
  onEdgesChange: OnEdgesChange;
  onConnect: OnConnect;

  /* ---------- Actions ---------- */
  setWorkerEnvironment: (worker: WorkerDetails) => void;

  loadNodeCatalogue: () => Promise<void>;

  loadGraphfromFile: (json_content: unknown) => void;

  saveGraphtoFile: (filename: string) => void;

  addNode: (node: Node) => void;

  setGraph: (nodes: Node[], edges: Edge[]) => void;

  clearGraph: () => void;

  closeErrorModal: () => void;

  cleanUp: () => void;

  preflight_run: () => Promise<any>

  updateNodeData: (nodeId: string, newData: Record<string, any>) => void;
  updateInputSimulatorData: (key: string, value: any) => void;

}

/* =========================================================
   IV. HELPERS
========================================================= */

function buildManifestMap(list: NodeManifest[]): Record<string, NodeManifest> {
  /* Return a json object that has format { {"classname": that class Manifest}, ...  } */
  const map: Record<string, NodeManifest> = {};

  for (const item of list) {
    map[item.class] = item;
  }

  return map;
}

function isGraphFile(value: any): value is GraphFile {
  return (
    value &&
    typeof value === "object" &&
    Array.isArray(value.nodes) &&
    Array.isArray(value.edges)
  );
}

function validateGraph(
  graph: GraphFile,
  catalogueMap: Record<string, NodeManifest>
): GraphValidationResult {
  const errors: string[] = [];

  /* ---------------------------
     A. Validate nodes
  ---------------------------- */

  for (const node of graph.nodes) {
    const className = (node as any).class || node?.data?.class;

    if (!className) {
      errors.push(`Node ${node.id} missing class`);
      continue;
    }

    const manifest = catalogueMap[className];

    if (!manifest) {
      errors.push(
        `Node class "${className}" not found in catalogue`
      );
      continue;
    }

    if (String(node.type) !== manifest.type) {
      errors.push(
        `Node ${node.id} type mismatch (${node.type} != ${manifest.type})`
      );
    }
  }

  /* ---------------------------
     B. Validate edges
  ---------------------------- */

  const nodeIds = new Set(graph.nodes.map((n) => n.id));

  for (const edge of graph.edges) {
    if (!nodeIds.has(edge.source)) {
      errors.push(
        `Edge source node not found: ${edge.source}`
      );
    }

    if (!nodeIds.has(edge.target)) {
      errors.push(
        `Edge target node not found: ${edge.target}`
      );
    }
  }

  return {
    ok: errors.length === 0,
    errors,
  };
}

/* =========================================================
   V. STORE
========================================================= */

export const useFlowStore = create<FlowState>()(
  persist( 
      (set,get) => ({
        /* ---------- Initial State ---------- */
        nodes: [],
        edges: [],

        this_worker_infor: null,

        nodeCatalogueList: [],
        nodeCatalogueMap: {},
        isCatalogueLoaded: false,

        isLoading: false,
        errorMessage: "",
        isErrorModalOpen: false,

        input_simulator_data: {},  //For preview of dummy input data in the debug panel
        result_inspector_data: {},

        /* =====================================================
          React Flow Handlers
        ===================================================== */

        onNodesChange: (changes) => {
          set({
            nodes: applyNodeChanges(changes, get().nodes),
          });
        },

        onEdgesChange: (changes) => {
          set({
            edges: applyEdgeChanges(changes, get().edges),
          });
        },

        onConnect: (connection) => {
          set({
            edges: addEdge(connection, get().edges),
          });
        },

        /* =====================================================
          Actions
        ===================================================== */

        setWorkerEnvironment: (worker) => {
          set({
            this_worker_infor: worker,
          });
        },

        loadNodeCatalogue: async () => {
          const worker = get().this_worker_infor;

          if (!worker?.selected_worker_id?.trim()) {
            set({
              errorMessage: "Worker environment not set",
              isErrorModalOpen: true,
            });
            return;
          }

          const workerId = worker.selected_worker_id;
          const isMaster = workerId === "master_gateway";

          try {
            set({ isLoading: true });

            const resp = await (
              isMaster
                ? NodeAPI.master_getCatalog()
                : NodeAPI.proxy_getCatalog(workerId)
            );

            const rawData = resp.data || resp; 
            const list = Array.isArray(rawData) ? rawData : []; // Ép kiểu an toàn 100%
            const map = buildManifestMap(list);

            set({
              nodeCatalogueList: list,
              nodeCatalogueMap: map,
              isCatalogueLoaded: true,
            });
        
          } catch (error: any) {
            set({
              errorMessage:
                error?.response?.data?.detail ||
                error.message ||
                "Load catalogue failed",
              isErrorModalOpen: true,
            });
          } finally {
            set({ isLoading: false });
          }
        },

        loadGraphfromFile: (json_content) => {
          /* 1. Shape check */
          if (!isGraphFile(json_content)) {
            set({
              errorMessage:
                "Invalid graph file format (nodes/edges missing)",
              isErrorModalOpen: true,
            });
            return;
          }

          /* 2. Need catalogue first */
          if (!get().isCatalogueLoaded) {
            set({
              errorMessage:
                "Node catalogue not loaded yet",
              isErrorModalOpen: true,
            });
            return;
          }

          /* 3. Validate */
          const result = validateGraph(
            json_content,
            get().nodeCatalogueMap
          );

          if (!result.ok) {
            set({
              errorMessage: result.errors.join("\n"),
              isErrorModalOpen: true,
            });
            return;
          }

          /* 4. Load graph */
          set({
            nodes: json_content.nodes,
            edges: json_content.edges,
          });
        },

        addNode: (node) => {
          set({
            nodes: [...get().nodes, node],
          });
        },

        setGraph: (nodes, edges) => {
          set({ nodes, edges });
        },

        clearGraph: () => {
          set({
            nodes: [],
            edges: [],
          });
        },

        closeErrorModal: () => {
          set({
            isErrorModalOpen: false,
            errorMessage: "",
          });
        },

        cleanUp: () => {
          set(initialState)
        },

        saveGraphtoFile: (filename : string) => {
          try {
            const { nodes, edges } = get();

            const payload = {
              nodes,
              edges
            };

            const json = JSON.stringify(payload, null, 2);

            const blob = new Blob(
              [json],
              { type: "application/json" }
            );

            const url = URL.createObjectURL(blob);

            const a = document.createElement("a");
            a.href = url;
            a.download = filename;
            a.click();

            URL.revokeObjectURL(url);
          } catch (error: any) {
            set({
              errorMessage:
                error.message || "Save graph failed",
              isErrorModalOpen: true
            });
          }
        },

        preflight_run: async () => {
          const worker = get().this_worker_infor;

          const graph : GraphFile = {
            nodes: get().nodes,
            edges: get().edges
          }

          const data : PreflightData = {
            graph : graph,
            preflight_payload : get().input_simulator_data
          }

          if (!worker?.selected_worker_id?.trim()) {
            set({
              errorMessage: "Worker environment not set",
              isErrorModalOpen: true,
            });
            return;
          }

          const workerId = worker.selected_worker_id;
          const isMaster = workerId === "master_gateway";

          try{
            const resp = await (
              isMaster
              ?NodeAPI.master_preflight_run(data)
              :NodeAPI.proxy_preflight_run(worker.selected_worker_id, data) 
            )
            
            set({result_inspector_data : resp.data})

          }
            catch (error: any) {
              set({
              errorMessage:
                error.response?.data?.detail || "Network Error",
                isErrorModalOpen: true
            });
            }
        },

        updateNodeData: (nodeId, newData) => {
          set((state) => ({
            nodes: state.nodes.map((node) => 
              node.id === nodeId 
                ? { ...node, data: { ...node.data, ...newData } } 
                : node
            )
          }));
        },

        updateInputSimulatorData: (key, value) => {
          set((state) => ({
            input_simulator_data: { ...state.input_simulator_data, [key]: value }
          }));
        },
      }),
      {
          name: "lambda-flow-storage", // Tên khóa lưu trong localStorage
          storage: createJSONStorage(() => localStorage),
          // CHỈ LƯU NHỮNG GÌ CẦN THIẾT (Quan trọng)
          partialize: (state) => ({
            this_worker_infor: state.this_worker_infor,
          }),
      }
    ) 
)



