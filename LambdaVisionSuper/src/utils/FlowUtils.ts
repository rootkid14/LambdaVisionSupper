// utils/flowUtils.ts
import { DataType } from "../Stores/FlowStore";

export const getPinColor = (type: DataType | string): string => {
  switch (type) {
    case 'boolean': return '!bg-red-500 !border-red-800'; // Đỏ
    case 'number': return '!bg-green-500 !border-green-800'; // Xanh lá
    case 'string': return '!bg-blue-400 !border-blue-700'; // Xanh dương nhạt
    
    // Các kiểu liên quan đến Mảng/Tensor
    case 'numpy_array': return '!bg-blue-600 !border-blue-900'; // Xanh dương đậm
    case 'list': return '!bg-purple-400 !border-purple-700'; // Tím nhạt
    case 'tensor': return '!bg-purple-600 !border-purple-900'; // Tím đậm
    
    // Các kiểu liên quan đến Cấu trúc/Object
    case 'dict': return '!bg-orange-400 !border-orange-700'; // Cam nhạt
    case 'json': return '!bg-orange-600 !border-orange-900'; // Cam đậm
    case 'object_ref': return '!bg-teal-500 !border-teal-800'; // Xanh mòng két
    
    // Các kiểu đặc biệt
    case 'base64': return '!bg-amber-400 !border-amber-700'; // Vàng hổ phách
    
    case 'any': return '!bg-slate-200 !border-slate-500'; // Trắng xám
    default: return '!bg-slate-400 !border-slate-600'; // Xám mặc định
  }
};