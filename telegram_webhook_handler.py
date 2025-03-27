import os
import logging
from flask import Flask, request, jsonify
import requests

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Telegram Bot Token from environment variable
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

# Flask app setup
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Telegram Notification Webhook is running!"

@app.route('/notify', methods=['POST'])
def notify_instructor():
    try:
        data = request.get_json()
        logger.info(f"📦 Incoming data from Airtable: {data}")

        # Extract and sanitize fields
        record_id = data.get("record_id", "Unknown")
        course = data.get("course", "Unknown")
        date = data.get("date", "Unknown")

        # Convert possible list fields to single string
        instructor = data.get("instructor", "")
        if isinstance(instructor, list):
            instructor = instructor[0]

        telegram_id = data.get("telegram_id", "")
        if isinstance(telegram_id, list):
            telegram_id = telegram_id[0]

        business = data.get("business", "")
        if isinstance(business, list):
            business = business[0]

        location = data.get("location", "")
        if isinstance(location, list):
            location = location[0]

        # Make address clickable if it's a URL
        if location.startswith("http"):
            location_text = f"[View Location]({location})"
        else:
            location_text = location

        # Format the message
        message = (
            f"👋 *Hi {instructor}*,\n\n"
            f"You’ve been assigned a course:\n\n"
            f"*Course:* {course}\n"
            f"*Date:* {date}\n"
            f"*Business:* {business}\n"
            f"*Location:* {location_text}\n\n"
            f"Please review your schedule."
        )

        logger.info(f"📢 Sending Telegram message to ID: {telegram_id}")

        # Send the Telegram message
        payload = {
            "chat_id": telegram_id,
            "text": message,
            "parse_mode": "Markdown"
        }

        response = requests.post(TELEGRAM_API_URL, json=payload)
        result = response.json()

        if response.status_code == 200 and result.get("ok"):
            logger.info(f"✅ Message sent successfully to {telegram_id}")
            return jsonify({"status": "success"}), 200
        else:
            logger.error(f"❌ Failed to send message: {result}")
            return jsonify({"status": "error", "details": result}), 500

    except Exception as e:
        logger.exception(f"🚨 Exception in /notify: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Entry point for Render
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
