import logging
import os
import tempfile

from google import genai
from telegram import ext as telegram_ext
import telegram

logging.basicConfig(level=logging.DEBUG, format="{asctime} {levelname:8s} {filename}:{lineno} {process}/{thread} {funcName}] {message}", style="{")
log = logging.getLogger("main")

gemini = genai.Client()

PROMPT = """
Process the attached audio file and generate a transcription, then summarize the transcription.

Requirements:
1. Identify distinct speakers by name, if possible, otherwise as "Speaker 1", "Speaker 2", etc.
2. Transcript summary should start with the one-sentence meeting summary, and a list of identified participants.
3. Provide terse meeting notes as bullet points, identify key discussion, action items, other important details.
4. Do not include the transcript, only the summary.
"""

async def handle_message(update: telegram.Update, _context: telegram_ext.ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    message_id = f"{update.message.chat_id}/{update.message.message_id}"
    if not update.message.audio:
        await update.message.reply_text("Your message did not contain an audio file")
        return
    status_message = await update.message.reply_text("Downloading file...")
    try:
        file = await update.message.audio.get_file()
        with tempfile.NamedTemporaryFile() as audio_file:
            await file.download_to_drive(audio_file.name)
            uploaded_file = gemini.files.upload(file=audio_file.name, config={"mime_type": "audio/mpeg"})
        await status_message.edit_text("Processing (this can take multiple minutes)...")
        interaction = gemini.interactions.create(
            model="gemini-3.5-flash",
            input=[
                {"type": "text", "text": PROMPT},
                {"type": "audio", "uri": uploaded_file.uri, "mime_type": uploaded_file.mime_type},
            ],
            stream=False,
        )
        output = interaction.output_text
        if not isinstance(output, str):
            log.error("message_id=%s, expected string interaction output, got %r", message_id, output)
            raise TypeError("unexpected interaction output")
        await status_message.edit_text(output)
    except Exception:
        log.exception("failed to process message %s", message_id)
        await status_message.edit_text(f"Failure to process audio. Provide this identifier for debugging: {message_id}")


token = os.getenv("TELEGRAM_TOKEN")
if not token:
    import sys
    log.fatal("TELEGRAM_TOKEN is not set")
    sys.exit(1)
app = telegram_ext.Application.builder().token(os.getenv("TELEGRAM_TOKEN")).build()
app.add_handler(telegram_ext.MessageHandler(filters=None, callback=handle_message))

if __name__ == "__main__":
    app.run_polling()
