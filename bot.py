import os
import re
import subprocess
import tempfile
import random
import string
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler

# Replace with your actual bot token
BOT_TOKEN = "7524183260:AAF-_yuvophw7q-DMxFStV5_aInKWhtdU1M"

# Function to generate a random password
def generate_password(length=12):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

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

    # Generate a temporary keystore
    keystore_path = os.path.join(temp_dir, "tempkeystore.jks")
    alias = "tempkey"
    password = generate_password()

    subprocess.run([
        "keytool", "-genkey", "-v",
        "-keystore", keystore_path,
        "-alias", alias,
        "-keyalg", "RSA",
        "-keysize", "2048",
        "-validity", "10000",
        "-storepass", password,
        "-keypass", password,
        "-dname", "CN=Temp, OU=None, O=None, L=None, ST=None, C=US"
    ], check=True)

    # Sign the APK
    apksigner_path = os.path.expanduser("~/android-sdk/build-tools/34.0.0/apksigner")
    subprocess.run([
        apksigner_path, "sign",
        "--ks", keystore_path,
        "--ks-pass", f"pass:{password}",
        "--key-pass", f"pass:{password}",
        "--ks-key-alias", alias,
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
