import logging
import os

from telegram import ext as telegram_ext
import telegram

logging.basicConfig(level=logging.DEBUG, format="{asctime} {levelname:8s} {filename}:{lineno} {process}/{thread} {funcName}] {message}", style="{")
log = logging.getLogger("main")

async def handle_message(update: telegram.Update, _context: telegram_ext.ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    if not update.message.audio:
        await update.message.reply_text("Your message did not contain an audio file")
        return
    await update.message.reply_text(f"Audio file: {update.message.audio.file_unique_id} {update.message.audio.file_size}")

token = os.getenv("TELEGRAM_TOKEN")
if not token:
    import sys
    log.fatal("TELEGRAM_TOKEN is not set")
    sys.exit(1)
app = telegram_ext.Application.builder().token(os.getenv("TELEGRAM_TOKEN")).build()
app.add_handler(telegram_ext.MessageHandler(filters=None, callback=handle_message))

if __name__ == "__main__":
    app.run_polling()
