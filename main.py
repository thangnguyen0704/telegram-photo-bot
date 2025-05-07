
import os
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import Update
from telegram.ext import ContextTypes
import gspread
from datetime import datetime
from collections import defaultdict
from fastapi import FastAPI, Request
import uvicorn

TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # Eg: https://yourapp.onrender.com

gc = gspread.service_account(filename="credentials.json")
sheet = gc.open_by_url(os.environ.get("SHEET_URL")).sheet1

app = FastAPI()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is online!")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.photo:
        file_id = update.message.photo[-1].file_id
        user = update.message.from_user.full_name
        group = update.effective_chat.title or update.effective_chat.id
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([now, group, user, file_id])
        await update.message.reply_text("Ảnh đã được ghi lại.")

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    date = datetime.now().strftime("%Y-%m-%d")
    data = sheet.get_all_records()
    summary = defaultdict(int)
    current_group = update.effective_chat.title

    for row in data:
        if row["Group"] == current_group and row["Time"].startswith(date):
            summary[row["User"]] += 1

    lines = [f"{k}: {v} photo(s)" for k, v in summary.items()]
    result = "Report for {}:\n{}".format(date, "\n".join(lines))
    await update.message.reply_text(result)

telegram_app = Application.builder().token(TOKEN).build()
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("report", report))
telegram_app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

@app.on_event("startup")
async def on_startup():
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.bot.set_webhook(f"{WEBHOOK_URL}/webhook/{TOKEN}")

@app.post("/webhook/{token}")
async def telegram_webhook(token: str, request: Request):
    if token != TOKEN:
        return {"error": "Invalid token"}
    data = await request.json()
    await telegram_app.update_queue.put(Update.de_json(data, telegram_app.bot))
    return {"ok": True}
