# Photoshop Studio Management System

Hệ thống quản lý studio Photoshop được xây dựng bằng Python Flask và MongoDB.

## Tính năng

- Gửi thông tin khách hàng và link ảnh
- Kiểm tra trạng thái xử lý ảnh
- Quản lý đơn hàng từ phía admin
- Phân loại đơn hàng với các nhãn khác nhau
- Tùy chỉnh giao diện client

## Công nghệ sử dụng

- **Backend**: Python Flask
- **Database**: MongoDB (Atlas hoặc Local)
- **Frontend**: HTML, CSS, JavaScript

## Cài đặt

1. Cài đặt các phụ thuộc:
   ```
   pip install -r requirements.txt
   ```

2. Cấu hình MongoDB:
   - Tạo file `.env` với chuỗi kết nối MongoDB:
   ```
   MONGO_URL=mongodb+srv://username:password@cluster.mongodb.net/database
   ```

3. Chạy ứng dụng:
   ```
   python app.py
   ```

## Triển khai

Ứng dụng có thể được triển khai lên các nền tảng như Railway với cấu hình MongoDB phù hợp.

## API Endpoints

### Client APIs
- `POST /api/submit` - Gửi thông tin đơn hàng mới
- `POST /api/check` - Kiểm tra trạng thái đơn hàng

### Admin APIs
- `POST /api/login` - Đăng nhập admin
- `GET /api/admin/data` - Lấy dữ liệu admin
- `POST /api/admin/update_ticket` - Cập nhật thông tin đơn hàng
- `POST /api/admin/delete_ticket` - Xóa đơn hàng
- `POST /api/admin/update_config` - Cập nhật cấu hình giao diện

## Bảo mật

Mật khẩu admin được hardcode:
- Username: `admin`
- Password: `studio123`

Nên thay đổi mật khẩu này trong môi trường sản xuất.