import os
from flask import Flask, request, jsonify
import requests
import logging
from datetime import datetime
import pytz

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
BASE_ID = os.getenv("AIRTABLE_BASE_ID")
TABLE_NAME = "Bookings"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

# Flask app
app = Flask(__name__)

@app.route("/")
def home():
    return "Telegram webhook is running!"

@app.route("/notify", methods=["POST"])
def notify_instructor():
    try:
        data = request.json
        logger.info(f"📦 Incoming data from Airtable: {data}")

        # Log raw values
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

        # Extract fields
        record_id = data.get("record_id")
        course = data.get("course", "Unknown course")
        date = data.get("date", "Unknown date")
        instructor = data.get("instructor", ["Instructor"])[0]
        first_name = instructor.split()[0] if instructor else "Instructor"
        telegram_id = data.get("telegram_id", [""])[0]
        business = data.get("business", ["Unknown business"])[0]
        location_name = data.get("location", [""])[0]
        full_address = data.get("full_address", [""])
        full_address = full_address[0] if isinstance(full_address, list) and full_address else "Not provided"
        map_link = data.get("map_link", [""])
        map_link = map_link[0] if isinstance(map_link, list) and map_link else ""
        instructor_fee = data.get("instructor_fee", 0)
        if isinstance(instructor_fee, list):
            instructor_fee = instructor_fee[0] if instructor_fee else 0

        location_display = f"<a href=\"{map_link}\">{full_address}</a>" if map_link else full_address

        # Compose Telegram message
        message = (
            f"👋 Hello <b>{first_name}</b>, you’ve been assigned a course:\n\n"
            f"📚 <b>Course:</b> {course}\n"
            f"📅 <b>Date:</b> {date}\n"
            f"🏢 <b>Business:</b> {business}\n"
            f"📍 <b>Location:</b> {location_display}\n"
            f"💷 <b>Instructor Fee:</b> £{instructor_fee}\n\n"
            f"💬 Any questions or comments, please contact the office.\n"
            f"📂 Full details of all courses assigned to you can be "
            f"<a href=\"https://bit.ly/4l7cljw\" disable_web_page_preview=\"true\">found in the database</a>."
        )

        # Send the Telegram message
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

            # ✅ Update Airtable record
            airtable_url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}/{record_id}"
            airtable_headers = {
                "Authorization": f"Bearer {AIRTABLE_API_KEY}",
                "Content-Type": "application/json"
            }

            now_utc = datetime.now(pytz.utc)
            timestamp = now_utc.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

            update_payload = {
                "fields": {
                    "Send notification Telegram to instructor": False,
                    "Date and time of Telegram message": timestamp
                }
            }

            update_response = requests.patch(airtable_url, json=update_payload, headers=airtable_headers)
            if update_response.status_code == 200:
                logger.info(f"✅ Airtable record {record_id} updated successfully.")
            else:
                logger.error(f"❌ Failed to update Airtable record {record_id}: {update_response.json()}")

            return jsonify({"status": "success"}), 200

        else:
            logger.error(f"❌ Failed to send message: {response_data}")
            return jsonify({"status": "error", "message": response_data}), 400

    except Exception as e:
        logger.exception("❌ Exception occurred during notification")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
