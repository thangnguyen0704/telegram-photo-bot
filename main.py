
import os
import logging
import datetime
import gspread
from fastapi import FastAPI, Request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from oauth2client.service_account import ServiceAccountCredentials

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(os.getenv("GOOGLE_SHEET_ID")).sheet1

def ensure_headers():
    headers = sheet.row_values(1)
    if headers != ["Date", "Group", "User", "Photo Count"]:
        sheet.clear()
        sheet.append_row(["Date", "Group", "User", "Photo Count"])

# Bot logic
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_headers()
    user = update.effective_user.first_name
    date = datetime.datetime.now().strftime('%Y-%m-%d')
    group = update.effective_chat.title or update.effective_chat.username or "PrivateChat"
    sheet.append_row([date, group, user, 1])

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if args:
        date = args[0]
    else:
        date = datetime.datetime.now().strftime('%Y-%m-%d')

    current_group = update.effective_chat.title or update.effective_chat.username or "PrivateChat"
    records = sheet.get_all_records()
    summary = {}
    for r in records:
        if r["Date"] == date and r["Group"] == current_group:
            user = r["User"]
            summary[user] = summary.get(user, 0) + int(r["Photo Count"])

    if not summary:
        await update.message.reply_text("No photos on {}.".format(date))
        return
    lines = ["{}: {} photo(s)".format(k, v) for k, v in summary.items()]
    result = "Report for {}:
{}".format(date, "\n".join(lines))
    await update.message.reply_text(result)

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is alive (webhook)!")

# FastAPI app + Telegram webhook setup
TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
application = Application.builder().bot(bot).build()
application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
application.add_handler(CommandHandler("report", report))
application.add_handler(CommandHandler("ping", ping))

# FastAPI server
app = FastAPI()

@app.post(f"/webhook/{TOKEN}")
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, bot)
    await application.process_update(update)
    return "ok"

@app.get("/")
def home():
    return {"status": "running"}
