import os
import re
import subprocess
import tempfile
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler

# Replace with your actual bot token
BOT_TOKEN = "7524183260:AAF-_yuvophw7q-DMxFStV5_aInKWhtdU1M"

# Path to the pre-existing demo keystore
DEMO_KEYSTORE_PATH = "/opt/render/project/src/demo_keystore.jks"  # Replace with your actual keystore file path on the server
DEMO_KEY_ALIAS = "demoalias"  # The alias used in your keystore
DEMO_KEY_PASSWORD = "demo_password"  # The password for the keystore
DEMO_KEY_PASS = "demo_password"  # The password for the key inside the keystore

# Function to clean the filename
def clean_filename(filename):
    name = filename.rsplit('.', 1)[0]  # Remove .apk
    name = re.split(r'[-]', name)[0].strip()  # Keep text before dash
    return f"{name}.apk"

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Send 'hello' or upload an APK file.")

# Hello message handler
async def say_hello(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello, world!")

# Document handler
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.document:
        return

    doc = update.message.document
    filename = doc.file_name

    # Check if the file is an APK
    if not filename.lower().endswith(".apk"):
        await update.message.reply_text("Please send a valid APK file.")
        return

    await update.message.reply_text("Processing your APK...")

    # Download the APK
    file = await context.bot.get_file(doc.file_id)
    temp_dir = tempfile.mkdtemp()
    apk_path = os.path.join(temp_dir, filename)
    await file.download_to_drive(custom_path=apk_path)

    # Clean the filename
    clean_name = clean_filename(filename)
    signed_apk_path = os.path.join(temp_dir, clean_name)

    # Sign the APK using the demo keystore
    apksigner_path = "/opt/render/project/src/android-sdk/build-tools/34.0.0/apksigner"  # Replace with the correct path
    subprocess.run([
        apksigner_path, "sign",
        "--ks", DEMO_KEYSTORE_PATH,
        "--ks-pass", f"pass:{DEMO_KEY_PASSWORD}",
        "--key-pass", f"pass:{DEMO_KEY_PASS}",
        "--ks-key-alias", DEMO_KEY_ALIAS,
        "--out", signed_apk_path,
        apk_path
    ], check=True)

    # Send back the signed APK
    await update.message.reply_document(document=open(signed_apk_path, "rb"), filename=clean_name)

# Main function to start the bot
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("(?i)^hello$"), say_hello))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    app.run_polling()

if __name__ == "__main__":
    main()
