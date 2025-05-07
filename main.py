import os
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Gspread setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
gc = gspread.authorize(creds)
sheet = gc.open_by_url(os.environ.get("SHEET_URL")).sheet1

# Nhận ảnh và ghi vào Google Sheet
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.photo:
        return

    group_name = update.effective_chat.title
    user = update.message.from_user.full_name
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    sheet.append_row([timestamp, group_name, user, "photo"])

# Trả báo cáo ảnh trong ngày của nhóm hiện tại
async def report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    current_group = update.effective_chat.title
    date = datetime.now().strftime("%Y-%m-%d")

    records = sheet.get_all_records()
    summary = {}

    for row in records:
        if row["Group"] == current_group and row["Time"].startswith(date):
            user = row["User"]
            summary[user] = summary.get(user, 0) + 1

    if not summary:
        await update.message.reply_text("Không có ảnh nào được gửi trong ngày hôm nay.")
        return

    lines = [f"{k}: {v} photo(s)" for k, v in summary.items()]
    result = "Report for {}:
{}".format(date, "\n".join(lines))
    await update.message.reply_text(result)

# Khởi tạo app
async def main() -> None:
    application = Application.builder().token(os.environ["BOT_TOKEN"]).build()
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(CommandHandler("report", report))
    await application.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
