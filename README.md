
# Telegram Webhook Bot with Google Sheets (Free Render version)

Bot dùng Webhook để ghi nhận ảnh Telegram + báo cáo số lượng ảnh mỗi ngày theo từng group vào Google Sheets.

## 🛠 Triển khai bot trên Render

### 1. Chuẩn bị
- Tạo 1 Telegram Bot trên @BotFather, lấy `BOT_TOKEN`
- Tạo 1 Google Sheet, lấy `GOOGLE_SHEET_ID` từ URL
- Tạo file `credentials.json` từ Google Cloud (Dịch vụ tài khoản - Service Account)

### 2. Deploy lên Render
- Vào [https://render.com](https://render.com)
- Chọn **"Web Service"**
- Chọn "Deploy from GitHub" (nếu push GitHub) hoặc upload thủ công

### 3. Cấu hình môi trường
Vào tab **Environment**, thêm biến:

- `BOT_TOKEN`: token của bot Telegram
- `GOOGLE_SHEET_ID`: mã Google Sheet
- Upload file `credentials.json` ở phần "File"

---

## ▶️ Khởi động bot
Render sẽ tự chạy `main.py` với `uvicorn`:
```bash
uvicorn main:app --host 0.0.0.0 --port 10000
```

Hoặc bạn cấu hình "Start Command" trong Render:
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

---

## 4. Thiết lập webhook cho Telegram bot

Chạy lệnh này sau khi bot đã chạy online (thay URL + BOT_TOKEN):

```bash
curl -X POST https://api.telegram.org/bot<BOT_TOKEN>/setWebhook?url=https://<render-app-url>/webhook/<BOT_TOKEN>
```

---

## 🧪 Kiểm tra bot hoạt động
Gửi `/ping` vào Telegram để test phản hồi  
Gửi `/report` để nhận báo cáo ảnh trong ngày hiện tại

