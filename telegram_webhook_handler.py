import os
from flask import Flask, request, jsonify
import requests
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

# Initialize Flask app
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Telegram Notification Webhook is running."

@app.route('/notify', methods=['POST'])
def notify_instructor():
    data = request.json
    logger.info(f"📦 Incoming data from Airtable: {data}")

    # Extract required fields
    telegram_id = data.get("telegram_id")
    course = data.get("course")
    date = data.get("matrix_date")
    location = data.get("location")
    business = data.get("business")
    instructor = data.get("instructor")

    if not telegram_id:
        logger.error("❌ Missing Telegram ID.")
        return jsonify({"status": "error", "message": "Missing Telegram ID"}), 400

    # Make location clickable
    location_text = location
    if location and location.startswith("http"):
        location_text = f"<a href='{location}'>Location</a>"

    # Compose the message
    message = (
        f"👋 Hello {instructor},\n\n"
        f"You’ve been assigned a course:\n\n"
        f"<b>📘 Course:</b> {course}\n"
        f"<b>📅 Date:</b> {date}\n"
        f"<b>🏢 Business:</b> {business}\n"
        f"<b>📍 Location:</b> {location_text}"
    )

    payload = {
        "chat_id": telegram_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }

    # Send Telegram message
    response = requests.post(TELEGRAM_API_URL, json=payload)
    if response.status_code == 200:
        logger.info(f"✅ Notification sent to {telegram_id}")
        return jsonify({"status": "success"}), 200
    else:
        logger.error(f"❌ Failed to send message: {response.text}")
        return jsonify({"status": "error", "message": response.text}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
