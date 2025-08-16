from dotenv import load_dotenv
import os

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
FLIGHT_SEARCH_INTERVAL = 60 * 60  # 90 minutes in seconds

flights_csv_path = '/home/aless/Documents/dataset_voli/flights.csv'
bash_script_disconnect = './nordvpn_disconnect.sh'
bash_script_connect = './nordvpn_connect.sh'
vpn_countries = ['Germany', 'Italy', 'Portugal', 'Spain', 'France']