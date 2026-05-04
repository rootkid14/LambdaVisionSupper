// src/utils/imageUtils.ts

export const ImageProcessing = {
  /**
   * Đọc file ảnh, ép kích thước (nếu vượt quá maxWidth), nén lại thành chuẩn JPEG/WebP
   * và trả về một File nhị phân mới sẵn sàng để gửi qua FormData hoặc WebSocket.
   * * @param file File ảnh gốc do người dùng upload hoặc từ Webcam
   * @param maxWidth Chiều rộng tối đa (Mặc định 1080 -  HD)
   * @param quality Chất lượng nén (0.0 đến 1.0, mặc định 0.8)
   * @param outputType Định dạng đầu ra ('image/jpeg' hoặc 'image/webp')
   * @returns Promise<File> Đối tượng File nhị phân đã được tối ưu
   */
  processImageForUpload: (
    file: File, 
    maxWidth: number = 1080, 
    quality: number = 0.8,
    outputType: 'image/jpeg' | 'image/webp' = 'image/jpeg'
  ): Promise<File> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      
      reader.onload = (event) => {
        const img = new Image();
        
        img.onload = () => {
          // 1. Tính toán kích thước mới (giữ nguyên tỷ lệ khung hình)
          let width = img.width;
          let height = img.height;

          if (width > maxWidth) {
            const ratio = maxWidth / width;
            width = maxWidth;
            height = Math.round(height * ratio);
          }

          // 2. Đưa lên thớt (Canvas) để xẻ thịt
          const canvas = document.createElement('canvas');
          canvas.width = width;
          canvas.height = height;
          const ctx = canvas.getContext('2d');

          // Xóa nền đen nếu có (quan trọng với ảnh PNG trong suốt ép sang JPEG)
          if (ctx) {
            ctx.fillStyle = '#FFFFFF';
            ctx.fillRect(0, 0, width, height);
            // Dùng thuật toán nội suy của trình duyệt để vẽ lại ảnh với size mới
            ctx.drawImage(img, 0, 0, width, height);
          }

          // 3. Ép xuất ra mảng nhị phân (Blob) thay vì Base64
          canvas.toBlob(
            (blob) => {
              if (blob) {
                // Đóng gói Blob thành đối tượng File y như lúc upload
                // Tên file được đổi đuôi cho chuẩn
                const extension = outputType === 'image/jpeg' ? '.jpg' : '.webp';
                const newFileName = file.name.replace(/\.[^/.]+$/, "") + "_optimized" + extension;
                
                const optimizedFile = new File([blob], newFileName, {
                  type: outputType,
                  lastModified: Date.now(),
                });
                
                resolve(optimizedFile);
              } else {
                reject(new Error("Lỗi khi tạo Blob từ Canvas"));
              }
            },
            outputType,
            quality
          );
        };

        img.onerror = () => reject(new Error("Không thể load hình ảnh vào thẻ Image"));
        img.src = event.target?.result as string;
      };

      reader.onerror = () => reject(new Error("Lỗi khi đọc file bằng FileReader"));
      reader.readAsDataURL(file);
    });
  }
};