import os
import logging
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# Logging
logging.basicConfig(level=logging.INFO)

# ENV
BOT_TOKEN = os.getenv("BOT_TOKEN")
SHEET_URL = os.getenv("SHEET_URL")

# Gspread setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
gc = gspread.authorize(creds)
sheet = gc.open_by_url(SHEET_URL).sheet1

# Telegram bot
application = Application.builder().token(BOT_TOKEN).build()

# FastAPI app
app = FastAPI()

# Ghi nhận ảnh gửi
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.photo:
        return
    vn_tz = timezone(timedelta(hours=7))
    timestamp = datetime.now(vn_tz).strftime("%Y-%m-%d %H:%M:%S")
    chat_id = str(update.effective_chat.id)
    chat_name = update.effective_chat.title or ""
    user = "{} - {}".format(update.effective_user.full_name, update.effective_user.username or update.effective_user.id)
    photo_count = len(update.message.photo)
    sheet.append_row([timestamp, chat_id, chat_name, user, str(photo_count)])

# Trả báo cáo
async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    vn_tz = timezone(timedelta(hours=7))
    today = datetime.now(vn_tz).strftime("%Y-%m-%d")

    if context.args:
        try:
            today = datetime.strptime(context.args[0], "%Y-%m-%d").strftime("%Y-%m-%d")
        except:
            await update.message.reply_text("Sai định dạng ngày. Dùng: /report YYYY-MM-DD")
            return

    data = sheet.get_all_values()
    if not data or len(data) < 2:
        await update.message.reply_text("Không có dữ liệu nào.")
        return

    headers = data[0]
    df = pd.DataFrame(data[1:], columns=headers)

    if "Date" not in df.columns or "Group ID" not in df.columns or "User" not in df.columns:
        await update.message.reply_text("Google Sheet thiếu cột bắt buộc.")
        return

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Group ID"] = df["Group ID"].astype(str)
    df = df[df["Group ID"] == str(update.effective_chat.id)]
    df = df[df["Date"].dt.strftime('%Y-%m-%d') == today]

    if df.empty:
        await update.message.reply_text("Không có ảnh nào được gửi trong ngày {}.".format(today))
        return

    summary = df["User"].value_counts().to_dict()
    lines = [f"{user}: {count} photo(s)" for user, count in summary.items()]
    result = "Report for {}:
{}".format(today, "\n".join(lines))
    await update.message.reply_text(result)

# Handlers
application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
application.add_handler(CommandHandler("report", report))

@app.post("/webhook/{token}")
async def telegram_webhook(token: str, request: Request):
    if token != BOT_TOKEN:
        return {"status": "unauthorized"}
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.initialize()
    await application.process_update(update)
    return {"status": "ok"}
