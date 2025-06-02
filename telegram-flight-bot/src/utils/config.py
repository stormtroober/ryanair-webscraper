from dotenv import load_dotenv
import os

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
FLIGHT_SEARCH_INTERVAL = 60 * 60  # 90 minutes in seconds