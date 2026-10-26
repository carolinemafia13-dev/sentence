import os
import logging
import threading
import time
from flask import Flask, jsonify
import requests

# === CONFIGURATION ===
TOKEN = os.environ.get('BOT_TOKEN')
PORT = int(os.environ.get('PORT', 8080))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === TELEGRAM API ===
def send_message(chat_id, text, parse_mode='Markdown'):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, json={
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode
        }, timeout=10)
    except Exception as e:
        logger.error(f"Send error: {e}")

def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    params = {'timeout': 30}
    if offset:
        params['offset'] = offset
    try:
        r = requests.get(url, params=params, timeout=35)
        if r.status_code == 200:
            return r.json().get('result', [])
    except Exception as e:
        logger.error(f"Get updates error: {e}")
    return []

def delete_webhook():
    try:
        requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook", timeout=10)
    except:
        pass

# === COMMAND HANDLERS ===
def handle_start(chat_id):
    text = """
👋 Welcome to *Quick Utility Bot*!

I perform useful calculations instantly without any external apps. 

📋 *Commands:*
/math [expression] - Calculate basic math (e.g. `/math 5*10`)
/percent [x] [y] - Find what percent X is of Y (e.g. `/percent 20 100`)
/bmi [weight_kg] [height_cm] - Calculate BMI (e.g. `/bmi 70 175`)
/help - Show this menu
    """
    send_message(chat_id, text)

def handle_math(chat_id, text):
    try:
        # Extract everything after "/math "
        expression = text.replace('/math', '').strip()
        if not expression:
            send_message(chat_id, "Usage: `/math 5*10`")
            return
        
        # Safe evaluation of basic math
        allowed_chars = set("0123456789+-*/(). ")
        if not set(expression).issubset(allowed_chars):
            send_message(chat_id, "❌ Error: Only numbers and basic operators (+, -, *, /) are allowed.")
            return

        result = eval(expression)
        send_message(chat_id, f"🧮 *Result:*\n`{expression} = {result}`")
    except Exception:
        send_message(chat_id, "❌ Invalid math expression. Example: `/math 15 * 4`")

def handle_percent(chat_id, text):
    try:
        parts = text.split()
        if len(parts) != 3:
            send_message(chat_id, "Usage: `/percent [part] [total]`\nExample: `/percent 20 100`")
            return
        
        part = float(parts[1])
        total = float(parts[2])
        
        if total == 0:
            send_message(chat_id, "❌ Total cannot be zero.")
            return
            
        result = (part / total) * 100
        send_message(chat_id, f"📊 *Percentage:*\n{part} is *{result:.2f}%* of {total}.")
    except ValueError:
        send_message(chat_id, "❌ Please enter valid numbers.")

def handle_bmi(chat_id, text):
    try:
        parts = text.split()
        if len(parts) != 3:
            send_message(chat_id, "Usage: `/bmi [weight_kg] [height_cm]`\nExample: `/bmi 70 175`")
            return
        
        weight = float(parts[1])
        height_cm = float(parts[2])
        
        height_m = height_cm / 100
        bmi = weight / (height_m * height_m)
        
        category = ""
        if bmi < 18.5:
            category = "Underweight"
        elif bmi < 25:
            category = "Normal weight"
        elif bmi < 30:
            category = "Overweight"
        else:
            category = "Obese"
            
        send_message(chat_id, f"⚖️ *BMI Result:*\nYour BMI is *{bmi:.1f}*\nCategory: *{category}*")
    except ValueError:
        send_message(chat_id, "❌ Please enter valid numbers.")

def handle_help(chat_id):
    text = """
📚 *Quick Utility Commands*

/math [expression] - Calculate basic math
/percent [part] [total] - Find percentage
/bmi [weight] [height] - Calculate BMI

Example:
`/math 100 / 4`
`/percent 25 200`
`/bmi 80 180`
    """
    send_message(chat_id, text)

# === POLLING ===
def process_updates():
    last_update_id = 0
    delete_webhook()
    logger.info("Polling started...")

    while True:
        try:
            updates = get_updates(last_update_id + 1 if last_update_id else None)
            for update in updates:
                uid = update.get('update_id')
                if uid:
                    last_update_id = uid

                if 'message' in update:
                    msg = update['message']
                    chat_id = msg['chat']['id']

                    if 'text' in msg:
                        text = msg['text']

                        if text.startswith('/start'):
                            handle_start(chat_id)
                        elif text.startswith('/math'):
                            handle_math(chat_id, text)
                        elif text.startswith('/percent'):
                            handle_percent(chat_id, text)
                        elif text.startswith('/bmi'):
                            handle_bmi(chat_id, text)
                        elif text.startswith('/help'):
                            handle_help(chat_id)
                        else:
                            send_message(chat_id, "Command not recognized. Use /help to see available commands.")
            time.sleep(2)
        except Exception as e:
            logger.error(f"Process updates error: {e}")
            time.sleep(5)

# === FLASK ===
app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return "<h1>Quick Utility Bot</h1><p>Status: Active</p>"

# === MAIN ===
def main():
    logger.info("Starting Quick Utility Bot...")
    threading.Thread(target=process_updates, daemon=True).start()
    app.run(host='0.0.0.0', port=PORT)

if __name__ == '__main__':
    main()
