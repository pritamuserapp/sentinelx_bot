import os
import random
import string
import firebase_admin
from firebase_admin import credentials, firestore
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler

# Replace with your actual bot token
BOT_TOKEN = "7524183260:AAF-_yuvophw7q-DMxFStV5_aInKWhtdU1M"

# Function to generate a random password
def generate_password(length=6):
    return ''.join(random.choices(string.digits, k=length))

# Initialize Firebase with the service account file
def init_firebase(service_account_file):
    if os.path.exists(service_account_file):
        cred = credentials.Certificate(service_account_file)
        firebase_admin.initialize_app(cred)
    else:
        raise FileNotFoundError(f"Service key file '{service_account_file}' not found.")

# Function to fetch password from Firebase
async def fetch_password(user_key):
    # Convert user_key to match the service key file format (RBL_1.json)
    service_account_path = f"firebase_keys/{user_key.replace(' ', '_')}.json"
    
    # Initialize Firebase
    try:
        init_firebase(service_account_path)
    except FileNotFoundError as e:
        return str(e)

    # Access the Firestore database
    db = firestore.client()

    # Fetch password from 'auth/admin_info/password' path
    try:
        doc_ref = db.collection('auth').document('admin_info')
        doc = doc_ref.get()

        if doc.exists:
            password = doc.to_dict().get('password')
            if password:
                return f"{user_key}: {password}"
            else:
                return f"No password found for {user_key}."
        else:
            return f"Admin info document not found for {user_key}."

    except Exception as e:
        return f"Error accessing Firebase: {str(e)}"

# Command handler for 'password' command
async def password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Expect user input like 'password RBL 1'
    user_input = update.message.text.strip()
    parts = user_input.split(' ')

    if len(parts) < 2 or parts[0].lower() != 'password':
        await update.message.reply_text("Please use the correct format: 'password <user_key>'.")
        return

    user_keys = parts[1].split(',')
    response = []

    for user_key in user_keys:
        result = await fetch_password(user_key.strip())
        response.append(result)

    # Reply with the results
    await update.message.reply_text('\n'.join(response))

# Command handler for 'change password' command
async def change_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()
    parts = user_input.split(' ')

    if len(parts) < 2 or parts[0].lower() != 'change':
        await update.message.reply_text("Please use the correct format: 'change password <user_key>'.")
        return

    user_keys = parts[2].split(',')
    new_password = generate_password()  # Generate a new random password

    # Process each user key and update the password
    response = []

    for user_key in user_keys:
        service_account_path = f"firebase_keys/{user_key.strip().replace(' ', '_')}.json"
        if os.path.exists(service_account_path):
            try:
                # Initialize Firebase with the correct service account file
                init_firebase(service_account_path)

                # Access Firestore and update password
                db = firestore.client()
                doc_ref = db.collection('auth').document('admin_info')
                doc_ref.update({
                    'password': new_password
                })

                response.append(f"Password for {user_key.strip()} has been changed to {new_password}.")
            except Exception as e:
                response.append(f"Error updating password for {user_key.strip()}: {str(e)}")
        else:
            response.append(f"Service key for {user_key.strip()} not found.")

    # Reply with the results
    await update.message.reply_text('\n'.join(response))

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Send 'hello' or upload an APK file.")

# Hello message handler
async def say_hello(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello, world!")

# Main function to start the bot
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("password", password))  # For password command
    app.add_handler(CommandHandler("change", change_password))  # For change password command
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("(?i)^hello$"), say_hello))

    app.run_polling()

if __name__ == "__main__":
    main()
