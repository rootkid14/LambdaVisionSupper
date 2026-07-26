from PIL import Image

def resize_and_concat(img1_path, img2_path, output_path):
    target_size = (1280, 960)

    # Hàm hỗ trợ resize
    def process_image(path):
        img = Image.open(path)
        # Resize về 1280x960
        return img.resize(target_size, Image.Resampling.LANCZOS)

    # 1. Resize cả 2 ảnh
    print(f"Đang xử lý resize ảnh 1...")
    img1 = process_image(img1_path)
    
    print(f"Đang xử lý resize ảnh 2...")
    img2 = process_image(img2_path)

    # 2. Tính toán kích thước ảnh kết quả
    # Sau khi resize, cả 2 ảnh đều là 1280x960
    # Vậy ảnh mới sẽ là 2560x960
    new_width = img1.width + img2.width
    new_height = img1.height # Vì đã resize nên chiều cao bằng nhau

    # 3. Tạo canvas mới
    new_img = Image.new('RGB', (new_width, new_height), (255, 255, 255))

    # 4. Dán ảnh vào
    new_img.paste(img1, (0, 0))
    new_img.paste(img2, (img1.width, 0))

    # 5. Lưu kết quả
    new_img.save(output_path)
    print(f"✅ Đã lưu ảnh kết quả (2560x960) tại: {output_path}")

# Sử dụng với đường dẫn của bạn
img1 = '/home/hieu/LambdaWebsite/my-react-ts-app/public/assets/images/test_1.png'
img2 = '/home/hieu/LambdaWebsite/my-react-ts-app/public/assets/images/test_2.jpg'
output = '/home/hieu/LambdaWebsite/my-react-ts-app/public/assets/images/result_combined.jpg'

resize_and_concat(img1, img2, output)