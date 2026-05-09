import { Node, Edge } from "@xyflow/react";
import { useTagDb, TagValue } from "./GlobalTagsStore";
import { useSequencerStore,
    NodeStartConfig,  
    SequencerNodeType, 
    NodeEndConfig, 
    NodeSplitConfig, 
    NodeJoinConfig, 
    NodeSwitchConfig, 
    NodeComputeConfig, 
    OperandType,
    NodeAndConfig, 
    NodeDelayConfig,
    NodeTagOvwrByValConfig,
    NodeExtractJSONConfig,
    NodeProcessConfig,
    NodeBuildJSONConfig,
    NodeScriptConfig,
    NodeWriteDBConfig,
    TokenValue} from "./SequencerStores";

import { NodeAPI } from "../../api/nodeApi";
import { DBEngineAPI } from "../../api/dbEngineApi";
import { useUIEngine } from '../UIEngineStores/InspectionStore';

interface BaseSequenceNode {
    execute(token_id: string) : Promise<void>;
    reset?(): void;
}

class NodeStart implements BaseSequenceNode {
    private next_node_id: string;
    private on_begin_map: Record<string, TagValue>;
    private engine: SequencerEngine;

    constructor(config: NodeStartConfig){
        this.next_node_id = config.next_node_id;
        this.on_begin_map = config.on_begin_map;
        this.engine = SequencerEngine.getInstance();
    }

    async execute(token_id : string): Promise<void> {
        //For start function, simply do the on begin data manipulation then move the token to the next node.(good for initializing first state)
        const tagStore = useTagDb.getState();
        for (const [key, value] of Object.entries(this.on_begin_map)) {
            //Write data from node config into the tag db table
            tagStore.writeTag(key, value);
        }
        //Move to next node
        this.engine.moveToken(token_id, this.next_node_id);
    }
}

class NodeEnd implements BaseSequenceNode {
    private on_end_map : Record<string, TagValue>;
    private engine : SequencerEngine;

    constructor(config: NodeEndConfig){
        this.on_end_map = config.on_end_map;
        this.engine = SequencerEngine.getInstance();
    }

    async execute(token_id : string): Promise<void> {
        // update the tag DB table with data from config then kill the token (good for cleaning up)
        const tagStore = useTagDb.getState();
        for (const[key, value] of Object.entries(this.on_end_map)){
            tagStore.writeTag(key, value);
        }
        this.engine.killToken(token_id);
    }
}

class NodeSplit implements BaseSequenceNode {
    private next_nodes_id_list : string[];
    private engine : SequencerEngine;

    constructor(config: NodeSplitConfig){
        this.next_nodes_id_list = config.next_nodes_id_list;
        this.engine = SequencerEngine.getInstance();
    }

    async execute(token_id : string): Promise<void> {
        //Spawn n new tokens for split 
        for (const node_id of this.next_nodes_id_list ){
            this.engine.spawnToken(node_id);
        }
        //then remove the previous single token
        this.engine.killToken(token_id);
    }
}

class NodeJoin implements BaseSequenceNode{
    private next_node_id: string;
    private token_count : number;
    private tokens_gathered : string[];
    private required_token_count : number;
    private engine: SequencerEngine;

    constructor(config: NodeJoinConfig){
        this.next_node_id = config.next_node_id;
        this.token_count = 0;
        this.tokens_gathered = [];
        this.required_token_count = config.required_tokens_count;
        this.engine = SequencerEngine.getInstance();
    }

    async execute(token_id : string): Promise<void> {
        // FIX 1: Dùng hàm .includes() của ES6, vứt bỏ vòng lặp for...in đi cho đời thanh thản
        if (this.tokens_gathered.includes(token_id)) {
            return;
        }
        
        this.tokens_gathered.push(token_id);
        
        // FIX 2: Bắt nó đứng phạt góc (Chuyển sang WAITING, không giết)
        this.engine.changeTokenStatus(token_id, "WAITING");
        this.token_count += 1;

        if (this.token_count === this.required_token_count){
            // BƯỚC 3: Đủ KPI rồi thì giết sạch các Token đang đứng chờ
            for (const t_id of this.tokens_gathered) {
                 this.engine.killToken(t_id);
            }
            
            // Và đẻ ra Token mới đi tiếp
            this.engine.spawnToken(this.next_node_id);
            this.token_count = 0;
            this.tokens_gathered = [];
        }
    }

    reset(): void {
        this.token_count = 0;
        this.tokens_gathered = [];
    }
}

class NodeSwitch implements BaseSequenceNode {
    private next_node_id_map: Record<string, string>; //value_to_compare : next_node_id
    private tag_id: string;
    private engine: SequencerEngine;

    constructor(config: NodeSwitchConfig){
        this.next_node_id_map = config.next_node_id_map;
        this.tag_id = config.tag_id;
        this.engine = SequencerEngine.getInstance();
    }

    async execute(token_id : string): Promise<void> {
        const tagStore = useTagDb.getState();
        const compared_val = String(tagStore.readTag(this.tag_id))
        for(const [key, value] of Object.entries(this.next_node_id_map)){
            if(compared_val === key) {
                this.engine.moveToken(token_id, value);
                return;
            }
        }
    }
}

const toNumber = (v: any): number => {
    // Helper function
    const n = Number(v);
    if (Number.isNaN(n)) return 0;
    return n;
};

class NodeCompute implements BaseSequenceNode {
    private next_node_id: string;
    private tag_id_a : string;
    private tag_id_b : string;
    private operand : OperandType;
    private target_tag_id: string;
    private engine: SequencerEngine;

    constructor(config: NodeComputeConfig){
        this.next_node_id = config.next_node_id;
        this.tag_id_a = config.tag_id_a;
        this.tag_id_b = config.tag_id_b;
        this.operand = config.operand
        this.target_tag_id = config.target_tag_id;
        this.engine = SequencerEngine.getInstance();
    }

    async execute(token_id : string): Promise<void> {
        const tagStore = useTagDb.getState();
        const a = toNumber(tagStore.readTag(this.tag_id_a));
        const b = toNumber(tagStore.readTag(this.tag_id_b));

        let result: number | boolean = 0;

        switch (this.operand) {
            case "+":
                result = a + b;
                break;

            case "-":
                result = a - b;
                break;

            case "*":
                result = a * b;
                break;

            case "/":
                result = b !== 0 ? a / b : 0;
                break;

            case ">":
                result = a > b;
                break;

            case ">=":
                result = a >= b;
                break;

            case "<":
                result = a < b;
                break;

            case "<=":
                result = a <= b;
                break;

            case "==":
                result = a === b;
                break;

            default:
                useSequencerStore.setState({isSequencerErrorModalOpen: true, SequencerErrorMessage: `Unsupported operand: ${this.operand}`})
                return;
        }

        tagStore.writeTag(this.target_tag_id, result);
        this.engine.moveToken(token_id, this.next_node_id);
    }
}

const toBoolean = (v: any): boolean => {
    if(typeof v === "boolean") return v;
    if(typeof v === "number") return v !== 0;
    if(typeof v === "string") return v.toLowerCase() === "true";
    if(v == null) return false;
    if(Array.isArray(v)) return v.length > 0;
    if(typeof v === "object") return Object.keys(v).length > 0;
    if(typeof v === "undefined") return false;
    return false
}

class NodeAnd implements BaseSequenceNode {
    private next_node_id : string;
    private engine: SequencerEngine;
    private tag_id_a: string;
    private tag_id_b: string;
    
    constructor(config: NodeAndConfig){
        this.next_node_id = config.next_node_id;
        this.engine = SequencerEngine.getInstance();
        this.tag_id_a = config.tag_id_a;
        this.tag_id_b = config.tag_id_b;
    }

    async execute(token_id : string): Promise<void> {
        const tagStore = useTagDb.getState();
        const a = toBoolean(tagStore.readTag(this.tag_id_a));
        const b = toBoolean(tagStore.readTag(this.tag_id_b));

        if ( a && b) {
            this.engine.moveToken(token_id, this.next_node_id);
        }
    }
}


class NodeOR implements BaseSequenceNode {
    private next_node_id : string;
    private engine: SequencerEngine;
    private tag_id_a: string;
    private tag_id_b: string;
    
    constructor(config: NodeAndConfig){
        this.next_node_id = config.next_node_id;
        this.engine = SequencerEngine.getInstance();
        this.tag_id_a = config.tag_id_a;
        this.tag_id_b = config.tag_id_b;
    }

    async execute(token_id : string): Promise<void> {
        const tagStore = useTagDb.getState();
        const a = toBoolean(tagStore.readTag(this.tag_id_a));
        const b = toBoolean(tagStore.readTag(this.tag_id_b));

        if ( a || b) {
            this.engine.moveToken(token_id, this.next_node_id);
        }
    }
}

class NodeDelay implements BaseSequenceNode {
    private next_node_id : string;
    private delay_duration: number;
    private engine: SequencerEngine;

    constructor(config: NodeDelayConfig){
        this.next_node_id = config.next_node_id;
        this.delay_duration = config.delay_duration;
        this.engine = SequencerEngine.getInstance();
    }

    async execute(token_id : string): Promise<void> {
        this.engine.changeTokenStatus(token_id, "PROCESSING");
        this.engine.schedule_move_token(token_id, this.delay_duration, this.next_node_id);
    }
}

class NodeTagOvwrByVal implements BaseSequenceNode {
    private next_node_id : string;
    private target_tag_id: string;
    private overwrite_value : any;
    private engine: SequencerEngine;

    constructor(config: NodeTagOvwrByValConfig){
        this.next_node_id = config.next_node_id;
        this.target_tag_id = config.target_tag_id;
        this.overwrite_value = config.ovwr_value;
        this.engine = SequencerEngine.getInstance();
    }

    async execute(token_id : string): Promise<void> {
        const tagStore = useTagDb.getState();
        tagStore.writeTag(this.target_tag_id, this.overwrite_value);
        this.engine.moveToken(token_id, this.next_node_id);
    }
}

class NodeTagOvwrByTag implements BaseSequenceNode {
    private next_node_id : string;
    private source_tag_id: string;
    private target_tag_id : string;
    private engine: SequencerEngine;

    constructor(config: NodeTagOvwrByTag){
        this.next_node_id = config.next_node_id;
        this.source_tag_id = config.source_tag_id
        this.target_tag_id = config.target_tag_id;
        this.engine = SequencerEngine.getInstance();
    }

    async execute(token_id : string): Promise<void> {
        const tagStore = useTagDb.getState();
        const value = tagStore.readTag(this.source_tag_id) ?? ""
        tagStore.writeTag(this.target_tag_id, value);
        this.engine.moveToken(token_id, this.next_node_id);
    }
}


function recursiveExtract(scriptObj: any, sourceObj: any, aliases: Record<string, string>, tagStore: any) {
    if (typeof scriptObj === 'object' && scriptObj !== null && typeof sourceObj === 'object' && sourceObj !== null) {
        for (const key in scriptObj) {
            const scriptVal = scriptObj[key];
            const sourceVal = sourceObj[key];
            
            // Nếu Script là một Alias String (VD: "@name")
            if (typeof scriptVal === 'string' && scriptVal.startsWith('@')) {
                if (scriptVal === '@ignore' || sourceVal === undefined) continue;
                
                const targetTag = aliases[scriptVal];
                if (targetTag) {
                    tagStore.writeTag(targetTag, sourceVal); // Móc từ Source nhét vào Tag
                }
            } 
            // Nếu Script là Object lồng nhau, tiếp tục đệ quy đi sâu vào
            else if (typeof scriptVal === 'object') {
                recursiveExtract(scriptVal, sourceVal, aliases, tagStore);
            }
        }
    }
}

function resolveJSONPath(obj: any, path: string): any {
    // 1. Kiểm tra đầu vào an toàn
    if (!path || typeof path !== 'string') return undefined;
    if (obj === null || obj === undefined) return undefined;

    // 2. Chuẩn hóa cấu trúc Path cực mạnh:
    // - Biến cấu trúc mảng arr[0] thành arr.0
    // - Cắt bỏ dấu chấm thừa ở đầu/cuối (vd: ".data.id" thành "data.id")
    const normalizedPath = path
        .replace(/\[(\w+)\]/g, '.$1')
        .replace(/^\.+|\.+$/g, '');

    const keys = normalizedPath.split('.');
    let current = obj;

    for (let i = 0; i < keys.length; i++) {
        const key = keys[i];

        // 3. SỬA BUG CHÍ MẠNG: Dùng === thay vì =
        if (current === null || current === undefined) {
            // Chủ động ném lỗi (Throw) để Node đang chạy bắt được và báo cho UI
            throw new Error(`Đường dẫn JSON bị đứt gãy tại khóa '${key}'. Dữ liệu tại đây không tồn tại.`);
        }

        // Đề phòng trường hợp cố tình trỏ vào một giá trị nguyên thủy (như số/chuỗi)
        if (typeof current !== 'object') {
            throw new Error(`Không thể tìm khóa '${key}' vì '${keys[i-1]}' không phải là Object/Array.`);
        }

        current = current[key];
    }

    return current;
}

class NodeExtractJSON implements BaseSequenceNode {
    private next_node_id: string;
    private source_tag_id: string;
    private aliases: Record<string, string>;
    private script: string;
    private engine: SequencerEngine;

    constructor(config: NodeExtractJSONConfig){
        this.next_node_id = config.next_node_id;
        this.source_tag_id = config.source_tag_id;
        this.aliases = config.aliases || {};
        this.script = config.script || "{}";
        this.engine = SequencerEngine.getInstance();
    }

    async execute(token_id : string): Promise<void> {
        const tagStore = useTagDb.getState();
        try {
            const sourceData = tagStore.readTag(this.source_tag_id);
            if (!sourceData || typeof sourceData !== 'object') {
                throw new Error(`Tag nguồn '${this.source_tag_id}' bị rỗng hoặc không phải JSON Object hợp lệ.`);
            }

            const scriptTemplate = JSON.parse(this.script); // Parse an toàn
            recursiveExtract(scriptTemplate, sourceData, this.aliases, tagStore);
            
            this.engine.moveToken(token_id, this.next_node_id);
        } catch (error: any) {
            useSequencerStore.setState({ isSequencerErrorModalOpen: true, SequencerErrorMessage: `Extract JSON Error: ${error.message}`});
            this.engine.changeTokenStatus(token_id, "PROCESSING"); 
        }
    }
}

function buildJSONFromPathMap(map: Record<string, any>, tagStore: any): any {
    const result: any = {};
    for (const path in map) {
        const tag_id = map[path];
        // Đọc GIÁ TRỊ THỰC TẾ từ Tag DB thay vì lấy tên tag
        const actual_value = tagStore.readTag(tag_id);

        // Bỏ qua nếu giá trị không tồn tại (undefined)
        if (actual_value === undefined) continue;

        // Chuẩn hóa path: cắt bỏ dấu '.' ở đầu (ví dụ: ".innum" -> "innum")
        const cleanPath = path.replace(/^\.+/, '');
        const keys = cleanPath.split('.');
        
        let current = result;
        for (let i = 0; i < keys.length; i++) {
            const key = keys[i];
            if (i === keys.length - 1) {
                current[key] = actual_value; // Nhét giá trị thực tế vào
            } else {
                if (!current[key] || typeof current[key] !== "object") {
                    current[key] = {};
                }
                current = current[key];
            }
        }
    }
    return result;
}

function recursiveBuild(scriptObj: any, aliases: Record<string, string>, tagStore: any): any {
    // Nếu là một Alias String -> Nhét dữ liệu từ Tag vào
    if (typeof scriptObj === 'string' && scriptObj.startsWith('@')) {
        if (scriptObj === '@ignore') return undefined; // Sẽ bị JSON.stringify lược bỏ sau này
        const sourceTag = aliases[scriptObj];
        return sourceTag ? tagStore.readTag(sourceTag) : null;
    } 
    // Nếu là Mảng -> Chạy lặp tạo mảng
    else if (Array.isArray(scriptObj)) {
        return scriptObj.map(item => recursiveBuild(item, aliases, tagStore));
    } 
    // Nếu là Object -> Duyệt tiếp tục
    else if (typeof scriptObj === 'object' && scriptObj !== null) {
        const result: any = {};
        for (const key in scriptObj) {
            const builtVal = recursiveBuild(scriptObj[key], aliases, tagStore);
            if (builtVal !== undefined) {
                result[key] = builtVal;
            }
        }
        return result;
    }
    // Nếu chỉ là Text/Number cứng ghi trong template thì giữ nguyên
    return scriptObj; 
}

class NodeBuildJSON implements BaseSequenceNode {
    private next_node_id: string;
    private target_tag_id: string;
    private aliases: Record<string, string>;
    private script: string;
    private engine: SequencerEngine;

    constructor(config: NodeBuildJSONConfig){
        this.next_node_id = config.next_node_id;
        this.target_tag_id = config.target_tag_id;
        this.aliases = config.aliases || {};
        this.script = config.script || "{}";
        this.engine = SequencerEngine.getInstance();
    }

    async execute(token_id : string): Promise<void> {
        const tagStore = useTagDb.getState();
        try {
            const scriptTemplate = JSON.parse(this.script); // Parse Template
            const builtJSON = recursiveBuild(scriptTemplate, this.aliases, tagStore);
            
            tagStore.writeTag(this.target_tag_id, builtJSON); // Ghi đè JSON mới tinh vào Tag đích
            this.engine.moveToken(token_id, this.next_node_id);
        } catch (error: any) {
            useSequencerStore.setState({ isSequencerErrorModalOpen: true, SequencerErrorMessage: `Build JSON Script Lỗi cú pháp: ${error.message}`});
            this.engine.changeTokenStatus(token_id, "PROCESSING"); 
        }
    }
}

class NodeProcess implements BaseSequenceNode {
    private next_node_id: string;
    private worker_id: string;
    private logic_object_id: string;
    private payload_formation_map: Record<string, any>;  //json path : tag
    private response_receive_map: Record<string, string>;  //json path : tag
    private engine: SequencerEngine

    constructor(config: NodeProcessConfig){
        this.next_node_id = config.next_node_id;
        this.worker_id = config.logic_object_info.worker_id;
        this.logic_object_id = config.logic_object_info.logic_object_id;
        this.payload_formation_map = config.payload_formation_map;
        this.response_receive_map = config.response_receive_map;
        this.engine = SequencerEngine.getInstance();
    }

    async execute(token_id : string): Promise<void> {
        const tagStore = useTagDb.getState();
        const payload = buildJSONFromPathMap(this.payload_formation_map, tagStore);
        const isMaster = this.worker_id === "master_gateway";
        try{
            //Require Worker to execute the logic object with payload
            this.engine.changeTokenStatus(token_id, "PROCESSING");
            const resp = await (
                isMaster
                ?NodeAPI.master_execute_logic(this.logic_object_id, payload)
                :NodeAPI.proxy_execute_logic(this.worker_id, this.logic_object_id, payload)
            )
            
            //If receive the good response => write results to tags table
            if(resp.success){
                const response_data = resp.data ?? {};
                for(const [path, tag] of Object.entries(this.response_receive_map)){
                    const extracted_data = resolveJSONPath(response_data, path)
                    tagStore.writeTag(tag, extracted_data);
                }
                this.engine.moveToken(token_id, this.next_node_id);
            }
            else {
                const error_message = `${this.logic_object_id} of ${this.worker_id} Error: faile at node ${resp.failed_node_id}, details: ${resp.error_message}`;
                useSequencerStore.setState({isSequencerErrorModalOpen: true, SequencerErrorMessage: error_message})
                useSequencerStore.getState().appendCompilerLog(error_message);
                return;
            }
        } catch (error: any) {
            const error_message = error.response?.data?.detail || `Network Error trying to call logic ${this.logic_object_id} from ${this.worker_id}`;
            useSequencerStore.setState({isSequencerErrorModalOpen: true, SequencerErrorMessage: error_message})
            useSequencerStore.getState().appendCompilerLog(error_message);
            return;
        }
    }

}


class NodePortalIn implements BaseSequenceNode {
    private next_node_id: string; // Chứa ID của Portal Out
    private engine: SequencerEngine;
    constructor(config: any){
        this.next_node_id = config.next_node_id;
        this.engine = SequencerEngine.getInstance();
    }
    async execute(token_id: string): Promise<void> {
        // Dịch chuyển tức thời Token sang cổng Out
        this.engine.moveToken(token_id, this.next_node_id);
    }
}

class NodePortalOut implements BaseSequenceNode {
    private next_node_id: string; // Chứa ID của khối tiếp theo thực sự
    private engine: SequencerEngine;
    constructor(config: any){
        this.next_node_id = config.next_node_id;
        this.engine = SequencerEngine.getInstance();
    }
    async execute(token_id: string): Promise<void> {
        this.engine.moveToken(token_id, this.next_node_id);
    }
}

class NodeScript implements BaseSequenceNode {
    private next_node_id: string;
    private input_aliases: Record<string, string>;
    private output_aliases: Record<string, string>;
    private script_content: string;
    private engine: SequencerEngine;

    constructor(config: NodeScriptConfig){
        this.next_node_id = config.next_node_id;
        this.input_aliases = config.input_aliases || {};
        this.output_aliases = config.output_aliases || {};
        this.script_content = config.script_content || "";
        this.engine = SequencerEngine.getInstance();
    }

    async execute(token_id: string): Promise<void> {
        const tagStore = useTagDb.getState();
        const IN: any = {};
        const OUT: any = {};

        try {
            // 1. Nhặt dữ liệu từ Tag đổ vào object IN (GIỮ NGUYÊN)
            for (const [alias, tagId] of Object.entries(this.input_aliases)) {
                IN[alias] = tagStore.readTag(tagId);
            }

            // ========================================================
            // 2. KHỞI TẠO ĐỐI TƯỢNG "UI" ĐỂ TRUY XUẤT NHANH COMPONENT
            // ========================================================
            const uiMap = useUIEngine.getState().components_map;
            
            const findComp = (query: string) => {
                if (uiMap[query]) return uiMap[query]; // Ưu tiên tìm bằng ID
                return Object.values(uiMap).find((c: any) => c.name === query); // Tìm bằng tên
            };

            const UI = {
                get: (query: string) => {
                    const comp = findComp(query);
                    if (!comp) return null;
                    return {
                        id: comp.id,
                        name: comp.name,
                        type: comp.type,
                        x: (comp as any).x,
                        y: (comp as any).y,
                        w: (comp as any).size_x, 
                        h: (comp as any).size_y,
                        rotation: (comp as any).rotation,
                        content: (comp as any).content,
                        isVisible: (comp as any).isVisible,
                        style: { ...((comp as any).style || {}) }
                    };
                },
                set: (query: string, props: any) => {
                    const comp = findComp(query);
                    if (!comp) return false;
                    
                    const updatePayload: any = { ...props };
                    // Map lại từ w, h sang chuẩn size_x, size_y của Engine
                    if (updatePayload.w !== undefined) { updatePayload.size_x = updatePayload.w; delete updatePayload.w; }
                    if (updatePayload.h !== undefined) { updatePayload.size_y = updatePayload.h; delete updatePayload.h; }
                    
                    // Giữ nguyên style cũ, chỉ ghi đè thuộc tính được yêu cầu
                    if (updatePayload.style) {
                        updatePayload.style = { ...(comp.style || {}), ...updatePayload.style };
                    }

                    useUIEngine.getState().updateComponentProps(comp.id, updatePayload);
                    return true;
                }
            };

            // 3. Ép kiểu tạo AsyncFunction với 3 tham số: IN, OUT, UI
            const AsyncFunction = Object.getPrototypeOf(async function(){}).constructor as any;
            const userCode = new AsyncFunction('IN', 'OUT', 'UI', this.script_content);

            // 4. Thực thi kịch bản
            await userCode(IN, OUT, UI);

            // 5. Lấy kết quả từ object OUT đổ ngược vào Tag (GIỮ NGUYÊN)
            for (const [alias, tagId] of Object.entries(this.output_aliases)) {
                if (OUT[alias] !== undefined) {
                    tagStore.writeTag(tagId, OUT[alias]);
                }
            }

            this.engine.moveToken(token_id, this.next_node_id);

        } catch (error: any) {
            const errorMsg = `JS Script Error: ${error.message}`;
            useSequencerStore.setState({ isSequencerErrorModalOpen: true, SequencerErrorMessage: errorMsg});
            useSequencerStore.getState().appendCompilerLog(`[RUNTIME ERROR] ${errorMsg}`);
            this.engine.changeTokenStatus(token_id, "PROCESSING");
        }
    }
}

// Sequencer Engine==============================================


interface Sequencer{
    live_node_objects: Record<string, BaseSequenceNode> //object uuid, instance
    
    cleanUpEngineMemory(): void;
    setEngineCompiled(): void;
    create_node_object(type: SequencerNodeType, config: any, node_id: string): void;
    tick(): void;
    moveToken(token_id : string, next_node_id: string): void;
    killToken(token_id: string): void;
    spawnToken(node_id: string): void;
}

interface ScheduledEventMoveToken {
    token_id: string;
    executeAt: number;
    next_node_id: string;
    finishDelayAt: number;
}


function dataURItoFile(dataURI: string, filename: string): File {
    const arr = dataURI.split(',');
    const mime = arr[0].match(/:(.*?);/)?.[1] || 'image/jpeg';
    const bstr = atob(arr[1]);
    let n = bstr.length;
    const u8arr = new Uint8Array(n);
    while (n--) {
        u8arr[n] = bstr.charCodeAt(n);
    }
    return new File([u8arr], filename, { type: mime });
}

class NodeWriteDB implements BaseSequenceNode {
    private next_node_id: string;
    private config: NodeWriteDBConfig;
    private engine: SequencerEngine;

    constructor(config: NodeWriteDBConfig){
        this.next_node_id = config.next_node_id;
        this.config = config;
        this.engine = SequencerEngine.getInstance();
    }

    async execute(token_id: string): Promise<void> {
        const tagStore = useTagDb.getState();
        const payloadData: Record<string, any> = {};
        const isMaster = this.config.worker_id === "master_gateway";

        this.engine.changeTokenStatus(token_id, "PROCESSING");

        try {
            for (const [colName, tagId] of Object.entries(this.config.mapping)) {
                let val;

                // ============================================
                // KIỂM TRA TỪ KHÓA AUTO THỜI GIAN
                // ============================================
                if (tagId === '__AUTO_TIME__') {
                    // Tạo chuỗi thời gian chuẩn ISO 8601 (Backend SQLAlchemy tự hiểu)
                    val = new Date().toISOString(); 
                } else {
                    // Đọc từ Global Tags như bình thường
                    val = tagStore.readTag(tagId as string);
                }
                
                // --- PHÉP THUẬT XỬ LÝ ẢNH ---
                if (this.config.image_columns[colName] && val && typeof val === 'string' && val.startsWith('data:image')) {
                    const filename = `img_${Date.now()}_${crypto.randomUUID().substring(0, 5)}.jpg`;
                    
                    // 1. Chỉ tạo File object
                    const fileObj = dataURItoFile(val, filename);
                    
                    // 2. Truyền thẳng fileObj vào API (Bỏ luôn đoạn tạo FormData ở đây)
                    const uploadRes = await (isMaster 
                        ? DBEngineAPI.master_uploadImage(fileObj) 
                        : DBEngineAPI.proxy_uploadImage(this.config.worker_id, fileObj));
                    
                    val = uploadRes.file_path; 
                }
                
                // Đóng gói vào Payload
                if (val !== undefined && val !== null && val !== "") {
                    payloadData[colName] = val;
                }
            }


            // GỌI API INSERT DATA
            const insertPayload = { table: this.config.table_name, data: payloadData };
            await (isMaster 
                ? DBEngineAPI.master_insertData(insertPayload) 
                : DBEngineAPI.proxy_insertData(this.config.worker_id, insertPayload));

            this.engine.moveToken(token_id, this.next_node_id);
        } catch (error: any) {
            const errorMsg = `WriteDB Error: ${error.message}`;
            useSequencerStore.setState({ isSequencerErrorModalOpen: true, SequencerErrorMessage: errorMsg});
            this.engine.changeTokenStatus(token_id, "PROCESSING");
        }
    }
}

const NodeClassRegistry: Record<string, any> = {
    "start": NodeStart,
    "end": NodeEnd,
    "split": NodeSplit,
    "join": NodeJoin,
    "switch": NodeSwitch,
    "comp": NodeCompute,
    "and": NodeAnd,
    "or": NodeOR,
    "delay": NodeDelay,
    "tov": NodeTagOvwrByVal,
    "tot": NodeTagOvwrByTag,
    "exjson": NodeExtractJSON,
    "buildjson": NodeBuildJSON,
    "proc": NodeProcess,
    "portal_in" : NodePortalIn,
    "portal_out" : NodePortalOut,
    "script": NodeScript,
    "writedb": NodeWriteDB
};

export class SequencerEngine implements Sequencer {
    private static instance: SequencerEngine | null = null;


    public static getInstance(): SequencerEngine {
        if (SequencerEngine.instance === null) {
            SequencerEngine.instance = new SequencerEngine();
        }
        return SequencerEngine.instance;
    }

    public token_list: Record<string, TokenValue> = useSequencerStore.getState().run_time_token_list; //token id: token value
    public live_node_objects: Record<string, BaseSequenceNode>;
    private timer_queue : ScheduledEventMoveToken[];
    private compiled : boolean;
    private isRunning: boolean;
    private start_node_id: string = "";

    private constructor(){
        this.live_node_objects = {};
        this.timer_queue = [];
        this.compiled = false;
        this.isRunning = false;
    }

    cleanUpEngineMemory(): void{
        this.compiled = false;
        this.token_list = {};
        this.live_node_objects = {};
        this.timer_queue = [];
    }

    setEngineCompiled(): void{
        this.compiled = true;
    }

    setStartNode(nodeId: string) {
        this.start_node_id = nodeId;
    }

    startEngine(): void {
        if (Object.keys(this.token_list).length === 0 && this.start_node_id) {
            this.spawnToken(this.start_node_id);
        }
        this.isRunning = true;
    }

    stopEngine(): void {
        this.isRunning = false;
        
        // Chỉ xóa Token và Hàng đợi Delay đang chạy dở
        this.token_list = {};
        this.timer_queue = [];
        
        // Gọi hàm reset() của tất cả các Node (nếu có) để xóa trí nhớ của lần chạy trước
        for (const node of Object.values(this.live_node_objects)) {
            if (typeof node.reset === 'function') {
                node.reset();
            }
        }
    }

    create_node_object(type: SequencerNodeType, config: any, node_id: string): void {
        const NodeClass = NodeClassRegistry[type];

        if (!NodeClass) {
            throw new Error(`[Engine Error] Unknown logic class for type: ${type}`);
        }

        this.live_node_objects[node_id] = new NodeClass(config);
    }

    tick(): void {
        if (!this.compiled || !this.isRunning) return;

        this.check_timer();

        for (const [token_id, token_value] of Object.entries(this.token_list)) {
            if (token_value.status === "READY") {
                this.live_node_objects[token_value.node_uuid].execute(token_id);
            }
        }

        // SET LẠI DATA CHO REACT RENDER
        useSequencerStore.setState({ run_time_token_list: { ...this.token_list } });

        // Đệ quy gọi lại chính nó sau x mili seccond
        setTimeout(() => this.tick(), useSequencerStore.getState().engine_tick_ms); 
    }

    moveToken(token_id: string, next_node_id: string): void {
        const token = this.token_list[token_id];

        if (!token) {
            useSequencerStore.setState({isSequencerErrorModalOpen: true, SequencerErrorMessage: `Token ${token_id} not found`})
            useSequencerStore.getState().appendCompilerLog(`Token ${token_id} not found`);
            return
        }

        const store = useSequencerStore.getState();
        const targetNode = store.nodes_lookup_map[next_node_id];

        this.token_list[token_id] = {
            ...token,
            node_uuid: next_node_id,
            status: "READY",
            color: "bg-green-600", // Xanh lá khi vừa đến
            x: targetNode ? targetNode.position.x + 10 : 0, 
            y: targetNode ? targetNode.position.y - 15 : 0,
        };
    }

    changeTokenStatus(token_id: string, new_status: 'READY' | 'PROCESSING' | 'WAITING' = "PROCESSING"): void {
        const token = this.token_list[token_id];
        if(!token) return;

        // FIX 3: Thêm logic cập nhật màu sắc dựa trên status
        let newColor = "bg-green-600";
        if (new_status === "PROCESSING") newColor = "bg-yellow-600";
        if (new_status === "WAITING") newColor = "bg-purple-500"; // Màu tím mộng mơ cho kẻ biết chờ đợi

        this.token_list[token_id] = {
            ...token,
            status: new_status,
            color: newColor 
        };
    }

    killToken(token_id: string): void {
        delete this.token_list[token_id]
    }

    spawnToken(nodeId: string): string {
        const token_id = crypto.randomUUID();
        const targetNode = useSequencerStore.getState().nodes_lookup_map[nodeId];

        this.token_list[token_id] = {
            node_uuid : nodeId,
            status: "READY",
            color: "bg-green-600",
            x: targetNode ? targetNode.position.x + 10 : 0,
            y: targetNode ? targetNode.position.y - 15 : 0,
        };
        return token_id;
    }

    schedule_move_token(token_id: string, delay: number,next_node_id: string): void {
        const execution_time = Date.now();
        const finish_delay_time = execution_time + (delay * 1000);
        const new_event : ScheduledEventMoveToken = {
            token_id : token_id,
            executeAt : execution_time,
            next_node_id: next_node_id,
            finishDelayAt: finish_delay_time
        }

        this.timer_queue.push(new_event);
    }

    check_timer() : void {
        for (let i = this.timer_queue.length - 1; i >= 0; i--){
            
            const item = this.timer_queue[i];

            if (Date.now() >= item.finishDelayAt){
                this.moveToken(item.token_id, item.next_node_id);
                this.timer_queue.splice(i, 1); // Delete the item and shift all the right side items.
            }
        }
    }
    
}


export class SequencerCompiler {
    private static isCompiling: boolean = false;

    // --- TÍNH NĂNG MỚI: Ép Timeout cho Promise để chống treo UI khi đứt mạng ---
    private static async fetchWithTimeout<T>(promise: Promise<T>, ms: number = 5000): Promise<T> {
        let timeoutId: ReturnType<typeof setTimeout>; 
        
        const timeoutPromise = new Promise<never>((_, reject) => {
            timeoutId = setTimeout(() => {
                reject(new Error(`Connection timed out after ${ms}ms`));
            }, ms);
        });
        return Promise.race([promise, timeoutPromise]).finally(() => clearTimeout(timeoutId));
    }

    static async compile(nodes: Node[], edges: Edge[]): Promise<boolean> {
        if (this.isCompiling) return false;
        this.isCompiling = true;
        const store = useSequencerStore.getState();
        store.appendCompilerLog(".............Start compiling ............");

        try {
            // Check Rule 1: Only 1 Start node
            const startNodes = nodes.filter(n => n.type === 'start')
            if (startNodes.length !== 1) {
                store.appendCompilerLog("Logic Error: Graph only allow to have 1 Start node!");
                this.isCompiling = false;
                return false;
            }

            // Check Rule 2: Any node has no input? (Ngoại trừ Start)
            for (const node of nodes) {
                if (node.type !== 'start') {
                    const hasIncoming = edges.some(e => e.target === node.id);
                    if (!hasIncoming) {
                        store.appendCompilerLog(`Warning: Node [${node.type}] has no input. Token will never reach it!`);
                    }
                }
            }

            // Check Rule 3: Liveness Check Thông Minh (Có Cache + Timeout)
            const processNodes = nodes.filter(n => n.type === 'proc');
            store.appendCompilerLog(`Checking connection status of ${processNodes.length} process nodes...`);

            const workerLogicsCache: Record<string, string[]> = {};

            for (const pNode of processNodes) {
                const config = (pNode.data?.sequencer_data as any)?.config as NodeProcessConfig;
                const workerId = config?.logic_object_info?.worker_id;
                const logicId = config?.logic_object_info?.logic_object_id;

                if (!workerId || !logicId) {
                    store.appendCompilerLog(`Graph Error: Process Node '${config?.node_title || pNode.id}' has not selected a Logic Object`);
                    this.isCompiling = false;
                    return false;
                }

                if (!workerLogicsCache[workerId]) {
                    try {
                        store.appendCompilerLog(`Pinging Server [${workerId}]...`);
                        const isMaster = workerId === 'master_gateway';
                        
                        const fetchPromise = isMaster ? 
                            NodeAPI.master_get_logic_id_list() : 
                            NodeAPI.proxy_get_logic_id_list(workerId);

                        // Timeout 4 giây
                        const availableLogics = await this.fetchWithTimeout<string[]>(fetchPromise, 4000);
                        workerLogicsCache[workerId] = availableLogics;
                        
                    } catch (err: any) {
                        store.appendCompilerLog(`API ERROR: Cannot Connect to Server [${workerId}]. Details: ${err.message || err}`);
                        this.isCompiling = false;
                        return false;
                    }
                }

                if (!workerLogicsCache[workerId].includes(logicId)) {
                    store.appendCompilerLog(`API Error: Logic Object '${logicId}' no longer exists on server '${workerId}'!`);
                    this.isCompiling = false;
                    return false;
                }
            }

            // SỬA LỖI LOG: Chuyển dòng log này ra khỏi vòng lặp
            store.appendCompilerLog("---------------------Validate Graph Successfully -> intializing Engine------------------");

            // Mapping Portal nodes 

            const portalOutMap: Record<string, string> = {}; 
            const portalOuts = nodes.filter(n => n.type === 'portal_out');
            
            for (const pOut of portalOuts) {
                const channel = (pOut.data?.sequencer_data as any)?.config?.channel_name;
                if (!channel) continue;
                if (portalOutMap[channel]) {
                    store.appendCompilerLog(`Graph Error: Kênh '${channel}' đang bị trùng lặp! Chỉ được phép có 1 Portal Out cho mỗi kênh.`);
                    this.isCompiling = false;
                    return false;
                }
                portalOutMap[channel] = pOut.id;
            }

            // ===============================================
            // Bước 2: Initialize Sequencer Engine & Graph
            // ===============================================
            const engine = SequencerEngine.getInstance();
            engine.stopEngine();
            engine.cleanUpEngineMemory();
            engine.setStartNode(startNodes[0].id);

            for (const node of nodes) {
                const config = (node.data?.sequencer_data as any)?.config || "";
                const outgoingEdges = edges.filter(e => e.source === node.id);

                if (node.type === "split") {
                    config.next_nodes_id_list = outgoingEdges.map(e => e.target);
                    engine.create_node_object("split", config, node.id);
                    
                } else if (node.type === "switch") {
                    const next_node_id_map: Record<string, string> = {};
                    outgoingEdges.forEach(e => {
                        // Sửa lỗi map switch: dùng lại config.cases
                        if (config.cases) {
                            const caseIndex = parseInt(e.sourceHandle?.replace('case-', '') || '0', 10);
                            const caseData = config.cases[caseIndex];
                            if (caseData) {
                                next_node_id_map[caseData.value] = e.target;
                            }
                        }
                    });
                    config.next_node_id_map = next_node_id_map;
                    engine.create_node_object("switch", config, node.id);
                    
                } else if (node.type === "join") {
                    const incomingEdges = edges.filter(e => e.target === node.id);
                    config.required_tokens_count = incomingEdges.length;
                    
                    if (outgoingEdges.length !== 1) {
                        store.appendCompilerLog(`Logic Error: node join [${node.id}] must have exactly 1 output`);
                        this.isCompiling = false;
                        return false;
                    }
                    config.next_node_id = outgoingEdges[0].target;
                    engine.create_node_object("join", config, node.id);
                    
                } else if (node.type === "end") {
                    // FIX CRASH: Node End tuyệt đối không được có đầu ra
                    if (outgoingEdges.length > 0) {
                        store.appendCompilerLog(`GRAPH Error: End node cannot have outgoing edges`);
                        this.isCompiling = false;
                        return false;
                    }
                    engine.create_node_object("end", config, node.id);

                } else if (node.type === "portal_in") {
                    const channel = config.channel_name;
                    const targetId = portalOutMap[channel];
                    if (!targetId) {
                        store.appendCompilerLog(`Graph Error: Portal In [${channel}] không tìm thấy Portal Out nào tương ứng!`);
                        this.isCompiling = false;
                        return false;
                    }
                    config.next_node_id = targetId; // Chỉa thẳng súng vào Portal Out
                    engine.create_node_object("portal_in", config, node.id);
                    
                } else if (node.type === "portal_out") {
                    if (outgoingEdges.length !== 1) {
                        store.appendCompilerLog(`GRAPH Error: Portal Out [${config.channel_name}] phải có đúng 1 output`);
                        this.isCompiling = false;
                        return false;
                    }
                    config.next_node_id = outgoingEdges[0].target;
                    engine.create_node_object("portal_out", config, node.id);
                    
                } else {
                    // CÁC NODE THÔNG THƯỜNG (Start, Proc, Delay, Comp, Logic...)
                    if (outgoingEdges.length !== 1) {
                        store.appendCompilerLog(`GRAPH Error: Node [${node.type}] must have exactly 1 output`);
                        this.isCompiling = false;
                        return false;
                    }
                    config.next_node_id = outgoingEdges[0].target;
                    engine.create_node_object(node.type as any, config, node.id);
                }
            }

            store.appendCompilerLog(`====================COMPILED SUCCESSFULLY=================`);
            engine.setEngineCompiled();
            this.isCompiling = false;
            return true;

        } catch (error: any) {
            // Bọc try..catch tổng để không bao giờ bị dính Silent Crash nữa
            store.appendCompilerLog(`CRITICAL COMPILER ERROR: ${error.message || error}`);
            console.error(error);
            this.isCompiling = false;
            return false;
        }
    }
}
