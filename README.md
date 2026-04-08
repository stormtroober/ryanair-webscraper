# Ryanair Flight Tracker & Telegram Bot

A powerful and automated tool designed to track Ryanair flight prices in real-time. This project features a robust Telegram bot that monitors specific routes and dates alerting you instantly when prices drop, and a fully featured Web Dashboard to manage your routes seamlessly.

## Key Features

- **Automated Web Scraping**: Runs scheduled checks every 90 minutes (configurable) to keep data fresh.
- **Web Dashboard (Django)**: A polished web interface to add/remove routes, monitor statuses, and view historical price trends using interactive charts.
- **Airport Autocomplete**: The web dashboard features a smart autocomplete to seamlessly search routes by city names, mapping them securely to their official IATA codes.
- **Instant Notifications**: The Telegram bot alerts you immediately when a price drop is detected.
- **VPN Integration**: Built-in support for VPN toggling to ensure reliable access and bypass rate limits.

## Getting Started

### Prerequisites
- Python 3.8+
- Chrome/Chromium & ChromeDriver (for Selenium automation)
- A VPN client configured (optional, for the VPN module)

### Installation

1.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configuration**
    Create a `config.env` file in the root directory:
    ```env
    TELEGRAM_BOT_TOKEN=your_telegram_bot_token
    FLIGHT_SEARCH_INTERVAL=5400
    ```

## Usage

### 1. Web Dashboard (Django App)

The web dashboard is the easiest way to manage your price alerts and visualize price changes visually.

Start the Django Server:
```bash
cd webapp
python manage.py makemigrations flights
python manage.py migrate
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` in your browser. From there you can:
- **Add routes**: Search from a database of global airports easily by city or code.
- **View Trends**: View visual line charts representing scraped price histories.
- **Live Scrape Control**: Trigger a manual background scrape using the web interface with Server-Sent Events (SSE) log streaming.

### 2. Telegram Bot

Run the bot for automated background checking and notifications to your mobile device:
```bash
python telegram_bot/bot.py
```

### Telegram Commands
| Command | Description |
|---------|-------------|
| `/start` | Initialize the bot and get valid commands. |
| `/start_search` | Start the automated flight monitoring cycle. |
| `/stop_search` | Stop the monitoring process. |
| `/status` | View current tracking status, active jobs, and cycle count. |

## Disclaimer
This tool is for educational purposes only. Use responsibly and adhere to the website's terms of service.
