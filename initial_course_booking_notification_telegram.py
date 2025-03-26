import os
import requests
import logging
import time

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Airtable API Details
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
BASE_ID = os.getenv("AIRTABLE_BASE_ID")
TABLE_NAME = "Bookings"

# Telegram API Details
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Airtable API URL
AIRTABLE_URL = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"

def fetch_bookings_to_notify():
    """Fetches bookings that need a Telegram notification."""
    headers = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}
    params = {
        "filterByFormula": 'AND({Send notification Telegram to instructor} = 1, {Course status} = "Scheduled", {Instructor Telegram ID} != "")'
    }

    response = requests.get(AIRTABLE_URL, headers=headers, params=params)
    
    if response.status_code == 200:
        return response.json().get("records", [])
    else:
        logger.error(f"❌ Failed to fetch bookings: {response.json()}")
        return []

def send_telegram_message(chat_id, message):
    """Sends a Telegram message to the instructor."""
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}

    response = requests.post(telegram_url, json=payload)
    
    if response.status_code == 200:
        logger.info(f"✅ Telegram message sent to {chat_id}")
        return True
    else:
        logger.error(f"❌ Failed to send message: {response.json()}")
        return False

def process_notifications():
    """Processes and sends notifications to instructors."""
    bookings = fetch_bookings_to_notify()

    if not bookings:
        logger.info("✅ No pending Telegram notifications.")
        return

    for booking in bookings:
        fields = booking["fields"]
        
        instructor_telegram_id = fields.get("Instructor Telegram ID", "")
        course_name = fields.get("Course (text)", "Unknown Course")
        matrix_date = fields.get("Matrix date", "Unknown Date")
        location = fields.get("Location", ["Unknown Location"])[0]  # Extract if linked
        business = fields.get("Business", ["Unknown Business"])[0]  # Extract if linked
        instructor_name = fields.get("Instructor", ["Unknown Instructor"])[0]

        message = (
            f"📢 **Course Booking Notification** 📢\n\n"
            f"👨‍🏫 **Instructor:** {instructor_name}\n"
            f"📅 **Date:** {matrix_date}\n"
            f"📖 **Course:** {course_name}\n"
            f"🏢 **Business:** {business}\n"
            f"📍 **Location:** {location}\n\n"
            f"✅ Please check your schedule and confirm attendance."
        )

        if send_telegram_message(instructor_telegram_id, message):
            # After sending, update Airtable: Uncheck "Send notification Telegram to instructor" and add a timestamp
            record_id = booking["id"]
            update_airtable(record_id)

def update_airtable(record_id):
    """Updates Airtable to uncheck 'Send notification Telegram to instructor' and add timestamp."""
    update_url = f"{AIRTABLE_URL}/{record_id}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }
    update_data = {
        "fields": {
            "Send notification Telegram to instructor": False,
            "Telegram Notification Sent": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    }

    response = requests.patch(update_url, json=update_data, headers=headers)

    if response.status_code == 200:
        logger.info(f"✅ Updated Airtable record {record_id}")
    else:
        logger.error(f"❌ Failed to update Airtable: {response.json()}")

if __name__ == "__main__":
    logger.info("🔄 Starting Telegram Notification Script...")
    process_notifications()
