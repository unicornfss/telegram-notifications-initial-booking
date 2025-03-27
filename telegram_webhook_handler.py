import os
from flask import Flask, request, jsonify
import requests
import logging

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

# Flask app setup
app = Flask(__name__)

@app.route("/")
def home():
    return "Telegram webhook is running!"

@app.route("/notify", methods=["POST"])
def notify_instructor():
    try:
        data = request.json
        logger.info(f"📦 Incoming data from Airtable: {data}")

         # Log each field individually
        logger.info(f"📌 Raw Fields:\n"
                    f"record_id: {data.get('record_id')}\n"
                    f"course: {data.get('course')}\n"
                    f"date: {data.get('date')}\n"
                    f"instructor: {data.get('instructor')}\n"
                    f"telegram_id: {data.get('telegram_id')}\n"
                    f"business: {data.get('business')}\n"
                    f"location: {data.get('location')}\n"
                    f"full_address: {data.get('full_address')}\n"
                    f"map_link: {data.get('map_link')}\n"
                    f"instructor_fee: {data.get('instructor_fee')}")

        # Extract fields from Airtable webhook
        record_id = data.get("record_id")
        course = data.get("course", "Unknown course")
        date = data.get("date", "Unknown date")
        instructor = data.get("instructor", ["Instructor"])[0]
        first_name = instructor.split()[0] if instructor else "Instructor"

        telegram_id = data.get("telegram_id", [""])[0]
        business = data.get("business", ["Unknown business"])[0]
        location_name = data.get("location", [""])[0]

        # New: Lookup fields for address and fee
        full_address = data.get("full_address", [""])
        full_address = full_address[0] if isinstance(full_address, list) and full_address else "Not provided"

        map_link = data.get("map_link", [""])
        map_link = map_link[0] if isinstance(map_link, list) and map_link else ""

        instructor_fee = data.get("instructor_fee", 0)

        # Create clickable address if map link exists
        location_display = f"<a href=\"{map_link}\">{full_address}</a>" if map_link else full_address

        # Compose message
        message = (
            f"👋 Hello <b>{first_name}</b>, you’ve been assigned a course:\n\n"
            f"📚 <b>Course:</b> {course}\n"
            f"📅 <b>Date:</b> {date}\n"
            f"🏢 <b>Business:</b> {business}\n"
            f"📍 <b>Location:</b> {location_display}\n"
            f"💷 <b>Instructor Fee:</b> £{instructor_fee}\n\n"
            f"💬 Any questions or comments, please contact the office.\n"
            f"📂 Full details of all courses assigned to you can be <a href=\"https://bit.ly/4l7cljw\" disable_web_page_preview=\"true\">found in the database</a>."
        )

        # Send Telegram message
        payload = {
            "chat_id": telegram_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }

        response = requests.post(TELEGRAM_API_URL, json=payload)
        response_data = response.json()

        if response.status_code == 200 and response_data.get("ok"):
            logger.info(f"✅ Message sent successfully to {telegram_id}")
            return jsonify({"status": "success"}), 200
        else:
            logger.error(f"❌ Failed to send message: {response_data}")
            return jsonify({"status": "error", "message": response_data}), 400

    except Exception as e:
        logger.exception("❌ Exception occurred during notification")
        return jsonify({"status": "error", "message": str(e)}), 500

# Only run if executed directly
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
