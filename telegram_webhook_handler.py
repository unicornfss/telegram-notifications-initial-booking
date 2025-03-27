import os
import logging
from flask import Flask, request, jsonify
import requests

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load Telegram bot token from environment
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

# Flask app
app = Flask(__name__)

@app.route('/')
def home():
    return "Telegram Webhook is running!"

@app.route('/notify', methods=['POST'])
def notify_instructor():
    try:
        data = request.get_json()
        logger.info(f"📦 Incoming data from Airtable: {data}")

        telegram_id = str(data.get("telegram_id", [""])[0]).strip()
        instructor_name = data.get("instructor", ["Instructor"])[0]
        first_name = instructor_name.split()[0] if instructor_name else "Instructor"
        course = data.get("course", "Unknown course")
        date = data.get("date", "Unknown date")
        business = data.get("business", ["Unknown business"])[0]
        fee = data.get("fee", "£0")
        address = data.get("address", "")
        map_url = data.get("map_url", "")

        # Construct location line
        if address and map_url:
            location_line = f"📍 Location: [{address}]({map_url})"
        elif address:
            location_line = f"📍 Location: {address}"
        else:
            location_line = "📍 Location: Not provided"

        message = (
            f"👋 Hello {first_name},\n\n"
            f"📅 You have been assigned a course:\n"
            f"🧾 *{course}*\n"
            f"📆 *{date}*\n"
            f"🏢 Business: *{business}*\n"
            f"{location_line}\n"
            f"💷 Instructor Fee: *{fee}*\n\n"
            f"ℹ️ Any questions or comments, please contact the office.\n"
            f"📚 Full details of all courses assigned to you can be [found in the database](https://bit.ly/4l7cljw)."
        )

        # Send Telegram message
        response = requests.post(TELEGRAM_API_URL, json={
            "chat_id": telegram_id,
            "text": message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        })

        if response.status_code == 200:
            logger.info(f"✅ Message sent successfully to {telegram_id}")
            return jsonify({"status": "success"}), 200
        else:
            logger.error(f"❌ Failed to send message: {response.json()}")
            return jsonify({"status": "failed", "error": response.json()}), 400

    except Exception as e:
        logger.exception("🚨 Error in /notify handler")
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
