import os
import logging
from datetime import datetime
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import gspread
from oauth2client.service_account import ServiceAccountCredentials

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

# Handlers
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.photo:
        return
    group = update.effective_chat.title or str(update.effective_chat.id)
    user = update.message.from_user.full_name
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([timestamp, group, user, "photo"])

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_group = update.effective_chat.title or str(update.effective_chat.id)
    date = datetime.now().strftime("%Y-%m-%d")
    records = sheet.get_all_records()
    summary = {}
    for row in records:
        if row.get("Group") == current_group and str(row.get("Time", "")).startswith(date):
            user = row.get("User", "Unknown")
            summary[user] = summary.get(user, 0) + 1
    if not summary:
        await update.message.reply_text("Không có ảnh nào được gửi trong ngày hôm nay.")
        return
    lines = [f"{k}: {v} photo(s)" for k, v in summary.items()]
    await update.message.reply_text("Report for {}:
{}".format(date, "\n".join(lines)))

# Add handlers
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
