# telegram_bot.py
import json
import socket
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# CHANGE THESE VALUES
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"   # Get from @BotFather
YOUR_TELEGRAM_ID = 123456789             # Your Telegram user ID (get from @userinfobot)
API_KEY = "your-secure-vsa-key-123"
DAEMON_PORT = 5555

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != YOUR_TELEGRAM_ID:
        await update.message.reply_text("Unauthorized.")
        return

    payload = {
        "auth_token": API_KEY,
        "intent": update.message.text,
        "twin": "brian_new"
    }

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('localhost', DAEMON_PORT))
            s.sendall(json.dumps(payload).encode())
            response = json.loads(s.recv(8192).decode())
        
        msg = f"Status: {response.get('status')}\nFidelity: {response.get('fidelity', 'N/A'):.4f}\nRoute: {response.get('route_id', 'N/A')}"
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f"Daemon error: {str(e)}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
