import os
import logging
from flask import Flask, request, jsonify
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Flask app
app = Flask(__name__)

def send_telegram_message(chat_id, text):
    """Send a message via Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    response = requests.post(url, json=payload)
    
    if response.status_code != 200:
        logger.error(f"❌ Failed to send message: {response.json()}")
        return False
    
    logger.info(f"✅ Message sent successfully to {chat_id}")
    return True

@app.route("/")
def home():
    return "Telegram webhook is live!"

@app.route("/notify", methods=["POST"])
def notify_instructor():
    """Handles incoming webhook from Airtable and sends a Telegram message."""
    try:
        data = request.json
        logger.info(f"📦 Incoming data from Airtable: {data}")

        # Extract values (handle lookups as lists)
        telegram_id_list = data.get("telegram_id", [])
        if not telegram_id_list or not telegram_id_list[0].isdigit():
            return jsonify({"error": "Missing or invalid Telegram ID"}), 400

        telegram_id = telegram_id_list[0]
        course = data.get("course", "Unknown course")
        date = data.get("date", "Unknown date")
        instructor_full_name = data.get("instructor", ["Instructor"])[0]
        instructor_first_name = instructor_full_name.split()[0]
        business = data.get("business", [""])[0]
        location_name = data.get("location_name", [""])[0]
        address = data.get("address", [""])[0]
        instructor_fee = data.get("instructor_fee", "")

        # Compose location with clickable link (Google Maps search)
        full_address = f"{location_name}, {address}".strip(", ")
        maps_url = f"https://www.google.com/maps/search/{requests.utils.quote(full_address)}"

        # Compose message
        message = (
            f"👋 Hello {instructor_first_name}, you've been assigned a new course:\n\n"
            f"📘 <b>Course:</b> {course}\n"
            f"📅 <b>Date:</b> {date}\n"
            f"🏢 <b>Business:</b> {business}\n"
            f"📍 <b>Location:</b> <a href='{maps_url}'>{full_address}</a>\n"
        )
        if instructor_fee:
            message += f"💷 <b>Instructor Fee:</b> £{instructor_fee}\n"

        message += (
            "\n💬 Any questions or comments, please contact the office. "
            "Full details of all courses assigned to you can be <a href='https://bit.ly/4l7cljw'>found in the database</a>."
        )

        # Send it
        send_telegram_message(telegram_id, message)
        return jsonify({"status": "success"}), 200

    except Exception as e:
        logger.exception("Error handling webhook")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
