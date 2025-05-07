
import logging
import datetime
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Kết nối Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(os.getenv("GOOGLE_SHEET_ID")).sheet1

# Hàm ghi nhận ảnh
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    date = datetime.datetime.now().strftime('%Y-%m-%d')
    sheet.append_row([date, user, 1])

# Báo cáo ngày cụ thể
async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if args:
        date = args[0]
    else:
        date = datetime.datetime.now().strftime('%Y-%m-%d')
    records = sheet.get_all_records()
    summary = {}
    for r in records:
        if r["Ngày"] == date:
            name = r["Tên người"]
            summary[name] = summary.get(name, 0) + int(r["Số ảnh"])
    if not summary:
        await update.message.reply_text(f"Không có ảnh nào ngày {date}.")
        return
    result = f"Báo cáo ngày {date}:
" + "\n".join([f"{k}: {v} ảnh" for k, v in summary.items()])
    await update.message.reply_text(result)

# Gửi báo cáo hàng ngày
def daily_report(app):
    records = sheet.get_all_records()
    today = datetime.datetime.now()
    cutoff = today - datetime.timedelta(days=30)
    filtered = [r for r in records if datetime.datetime.strptime(r["Ngày"], "%Y-%m-%d") >= cutoff]
    # Tùy chỉnh nếu muốn lưu CSV tại đây hoặc gửi qua Telegram

# Scheduler tự động
def start_scheduler(app):
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: daily_report(app), 'cron', hour=23, minute=59)
    scheduler.start()

# Khởi chạy bot
if __name__ == '__main__':
    bot_token = os.getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(bot_token).build()
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CommandHandler("baocao", report))
    start_scheduler(app)
    app.run_polling()
