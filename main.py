
import logging
import datetime
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Connect to Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(os.getenv("GOOGLE_SHEET_ID")).sheet1

# Ensure headers exist
def ensure_headers():
    try:
        headers = sheet.row_values(1)
        if headers != ["Date", "Group", "User", "Photo Count"]:
            sheet.clear()
            sheet.append_row(["Date", "Group", "User", "Photo Count"])
    except Exception as e:
        logger.error(f"Error ensuring headers: {e}")

# Handle photo uploads
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_headers()
    user = update.effective_user.first_name
    date = datetime.datetime.now().strftime('%Y-%m-%d')
    group = update.effective_chat.title or update.effective_chat.username or "PrivateChat"
    sheet.append_row([date, group, user, 1])

# Report command
async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if args:
        date = args[0]
    else:
        date = datetime.datetime.now().strftime('%Y-%m-%d')
    records = sheet.get_all_records()
    summary = {}
    for r in records:
        if r["Date"] == date:
            group = r["Group"]
            user = r["User"]
            key = "[{}] {}".format(group, user)
            summary[key] = summary.get(key, 0) + int(r["Photo Count"])
    if not summary:
        await update.message.reply_text("No photos on {}.".format(date))
        return
    lines = ["{}: {} photo(s)".format(k, v) for k, v in summary.items()]
    result = "Report for {}:
{}".format(date, "
".join(lines))
    await update.message.reply_text(result)

# Ping command
async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is alive!")

# Daily summary function
def daily_report(app):
    ensure_headers()
    records = sheet.get_all_records()
    today = datetime.datetime.now()
    cutoff = today - datetime.timedelta(days=30)
    _ = [r for r in records if datetime.datetime.strptime(r["Date"], "%Y-%m-%d") >= cutoff]

# Schedule daily job
def start_scheduler(app):
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: daily_report(app), 'cron', hour=23, minute=59)
    scheduler.start()

# Run the bot
if __name__ == '__main__':
    bot_token = os.getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(bot_token).build()
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CommandHandler("report", report))
    app.add_handler(CommandHandler("ping", ping))
    start_scheduler(app)
    app.run_polling()
