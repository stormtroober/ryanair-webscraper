from dotenv import load_dotenv
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / 'config.env')

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
FLIGHT_SEARCH_INTERVAL = 60 * 60  # 90 minutes in seconds

bash_script_disconnect = str(BASE_DIR / 'nordvpn_disconnect.sh')
bash_script_connect = str(BASE_DIR / 'nordvpn_connect.sh')
vpn_countries = ['Germany', 'Italy', 'Portugal', 'Spain', 'France']