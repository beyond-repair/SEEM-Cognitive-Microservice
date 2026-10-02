# telegram_bot.py
# Optional front end. The CLI and daemon do not need Telegram.
import json
import os
import socket
import sys

try:
    from telegram import Update
    from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
except ImportError:
    print("Optional dependency missing. pip install -r requirements-telegram.txt", file=sys.stderr)
    sys.exit(1)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
YOUR_TELEGRAM_ID = os.environ.get("TELEGRAM_USER_ID", "")


def load_local_config():
    path = os.environ.get("SEEM_CONFIG", "config.json")
    if not os.path.isfile(path):
        path = "config.json.example"
    with open(path) as handle:
        return json.load(handle)


CFG = load_local_config()
API_KEY = CFG.get("api_key", "your-secure-vsa-key-123")
DAEMON_PORT = int(CFG.get("daemon_port", 5555))


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != str(YOUR_TELEGRAM_ID):
        await update.message.reply_text("Unauthorized.")
        return

    payload = {
        "auth_token": API_KEY,
        "intent": update.message.text,
        "twin": os.environ.get("SEEM_TWIN", "brian_new"),
    }

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect(("127.0.0.1", DAEMON_PORT))
            sock.sendall(json.dumps(payload).encode())
            response = json.loads(sock.recv(8192).decode())
        fidelity = response.get("fidelity")
        fidelity_text = "n/a" if fidelity is None else f"{float(fidelity):.4f}"
        msg = (
            f"Status: {response.get('status')}\n"
            f"Fidelity: {fidelity_text}\n"
            f"Route: {response.get('route_id')}"
        )
        await update.message.reply_text(msg)
    except Exception as exc:
        await update.message.reply_text(f"Daemon error: {exc}")


if __name__ == "__main__":
    if not TOKEN:
        print("Set TELEGRAM_BOT_TOKEN and TELEGRAM_USER_ID. Core CLI does not need Telegram.", file=sys.stderr)
        sys.exit(1)
    if not YOUR_TELEGRAM_ID:
        print("Set TELEGRAM_USER_ID to your numeric Telegram user id.", file=sys.stderr)
        sys.exit(1)
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
