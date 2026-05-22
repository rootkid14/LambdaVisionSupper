// File: src/UI_Engine/SequencerComponents/ScriptApiDocs.ts

export const SCRIPT_API_DOCS_MD = `# LAMBDA VISION - SCRIPTING & AGENTIC API DOCUMENTATION

## I. TỔNG QUAN (OVERVIEW)
Hệ thống Lambda Vision sử dụng JIT (Just-In-Time) Compiler để thực thi mã Javascript tại Runtime.
Môi trường Sandbox cung cấp 4 đối tượng cốt lõi: \`IN\`, \`OUT\`, \`UI\`, và \`ENGINE\`.

---

## II. ĐỐI TƯỢNG DỮ LIỆU (IN & OUT)
Dùng để giao tiếp với Global Tags thông qua cơ chế Alias (Ánh xạ biến).

### 1. IN (Read-only)
- **Mục đích:** Đọc giá trị từ Tag vào kịch bản.
- **Ví dụ:**
  \`\`\`javascript
  let speed = IN.motor_speed;
  if (speed > 100) { /* ... */ }
  \`\`\`

### 2. OUT (Write-only)
- **Mục đích:** Đẩy kết quả tính toán ra Global Tags. Chỉ những biến được khai báo bên cột Output mới được ghi đè.
- **Ví dụ:**
  \`\`\`javascript
  OUT.alert_status = "WARNING";
  \`\`\`

---

## III. ĐỐI TƯỢNG GIAO DIỆN (UI)
Cho phép Script can thiệp, thay đổi thuộc tính của các Component trên màn hình theo thời gian thực.

### 1. UI.get(identity: string)
- **Mục đích:** Lấy thông tin hiện tại của một Component.
- **Ví dụ:** \`let box = UI.get("BBOX_1");\`

### 2. UI.set(identity: string, props: object)
- **Mục đích:** Cập nhật thuộc tính (x, y, w, h, style...).
- **Ví dụ:**
  \`\`\`javascript
  UI.set("Text_Status", { 
      content: "SYSTEM HALTED", 
      style: { fontColor: "#f28b82" } 
  });
  \`\`\`

---

## IV. ĐỐI TƯỢNG ĐIỀU PHỐI (ENGINE)
Cung cấp quyền năng Multi-Agent, thao túng trực tiếp các Token đang chạy trên Sequencer Graph.
*Lưu ý: Bạn phải đặt tên (Identity) cho các Node để sử dụng bộ API này.*

### 1. Cơ chế Nhãn Dán (Labeling)
Dùng để phân loại Token theo luồng nghiệp vụ.
- \`ENGINE.addLabel(label_name: string)\`: Dán nhãn cho Token hiện tại.
- \`ENGINE.removeLabel(label_name: string)\`: Gỡ nhãn.
- \`ENGINE.hasLabel(label_name: string) -> boolean\`: Kiểm tra nhãn.

### 2. Truy vấn (Querying)
Quét toàn hệ thống để tìm các Token thỏa mãn điều kiện. Trả về mảng các UUID của Token.
- \`ENGINE.queryByLabel(label_name: string) -> string[]\`
- \`ENGINE.queryByHistory(node_identity: string) -> string[]\`

### 3. Điều phối Không gian (Teleport & Spawn)
- \`ENGINE.spawnAt(node_identity: string)\`: Tạo một Token mới tinh xuất hiện tại Node được chỉ định.
- \`ENGINE.moveAll(from_node_identity: string, to_node_identity: string)\`: Ép toàn bộ Token đang kẹt ở Node A bay thẳng sang Node B.
- \`ENGINE.hijack(token_id: string, target_node_identity: string)\`: Bắt cóc 1 Token cụ thể và ném sang Node khác (Token sẽ đổi sang màu Đỏ).

### 4. Hủy diệt (Destruction)
- \`ENGINE.kill(token_id: string)\`
- \`ENGINE.killAt(node_identity: string) -> number\`: Xóa sổ mọi Token đang đứng tại Node này. Trả về số lượng đã giết.
- \`ENGINE.killAllByLabel(label_name: string) -> number\`: Xóa sổ toàn bộ Token mang nhãn này trên toàn hệ thống.

---
*Tài liệu được sinh tự động từ hệ thống Lambda Vision UI Editor.*
`;