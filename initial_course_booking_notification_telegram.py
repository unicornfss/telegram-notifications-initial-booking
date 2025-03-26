import os
import requests
import logging
import time

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Telegram & Airtable Config
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
BASE_ID = os.getenv("AIRTABLE_BASE_ID")
TABLE_NAME = "Bookings"

# Airtable API URL
AIRTABLE_URL = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"


def fetch_bookings_to_notify():
    """Fetches bookings that need a Telegram notification."""
    headers = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}
    params = {
        "filterByFormula": 'AND({Send notification Telegram to instructor} = 1, {Course status} = "Scheduled", {Instructor Telegram ID} != "")'
    }

    response = requests.get(AIRTABLE_URL, headers=headers, params=params)
    
    if response.status_code == 200:
        bookings = response.json().get("records", [])
        logger.info(f"✅ Found {len(bookings)} bookings to notify.")
        return bookings
    else:
        logger.error(f"❌ Failed to fetch bookings: {response.json()}")
        return []


def send_telegram_message(telegram_id, message):
    """Sends a Telegram message to the given Telegram ID."""
    logger.info(f"📢 Sending Telegram message to ID: {telegram_id}")

    payload = {"chat_id": telegram_id, "text": message}
    response = requests.post(TELEGRAM_API_URL, json=payload)

    if response.status_code == 200:
        logger.info(f"✅ Message sent successfully to {telegram_id}")
        return True
    else:
        logger.error(f"❌ Failed to send message: {response.json()}")
        return False


def update_airtable_record(record_id):
    """Updates the Airtable record to mark the notification as sent."""
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "fields": {
            "Send notification Telegram to instructor": False,
            "Notification Sent Timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    }

    response = requests.patch(f"{AIRTABLE_URL}/{record_id}", json=data, headers=headers)
    
    if response.status_code == 200:
        logger.info(f"✅ Record {record_id} updated successfully.")
    else:
        logger.error(f"❌ Failed to update record {record_id}: {response.json()}")


def process_notifications():
    """Processes all pending notifications."""
    bookings = fetch_bookings_to_notify()

    if not bookings:
        logger.info("✅ No pending Telegram notifications.")
        return

    for record in bookings:
        fields = record["fields"]
        record_id = record["id"]

        # Extract details safely
        telegram_id_list = fields.get("Instructor Telegram ID", [])
        telegram_id = telegram_id_list[0] if isinstance(telegram_id_list, list) and telegram_id_list else ""

        course_name = fields.get("Course (text)", "Unknown Course")
        booking_date = fields.get("Matrix date", "Unknown Date")
        location = fields.get("Location", "Unknown Location")
        business = fields.get("Business", "Unknown Business")

        # Debug: Print all extracted values
        logger.info(f"📋 Extracted Data - ID: {telegram_id}, Course: {course_name}, Date: {booking_date}, Location: {location}, Business: {business}")

        if not telegram_id:
            logger.error(f"⚠️ Skipping notification for {course_name} - No valid Telegram ID found.")
            continue

        # Construct message
        message = (
            f"📅 *New Course Booking*\n\n"
            f"📖 Course: {course_name}\n"
            f"📆 Date: {booking_date}\n"
            f"📍 Location: {location}\n"
            f"🏢 Business: {business}\n\n"
            f"✅ Please check your schedule."
        )

        # Send message
        if send_telegram_message(telegram_id, message):
            update_airtable_record(record_id)


if __name__ == "__main__":
    logger.info("🔄 Starting Telegram Notification Script...")
    process_notifications()
