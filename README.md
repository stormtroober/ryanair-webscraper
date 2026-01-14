# Ryanair Flight Tracker & Telegram Bot

A powerful and automated tool designed to track Ryanair flight prices in real-time. This project features a robust Telegram bot that monitors specific routes and dates, alerting you instantly when prices drop.

## Key Features

- **Automated Scraping**: Runs scheduled checks every 90 minutes (configurable) to keep data fresh.
- **Instant Notifications**: Receives Telegram alerts immediately when a price drop is detected.
- **VPN Integration**: Built-in support for VPN toggling to ensure reliable access and data accuracy.
- **Status Reporting**: Check the current monitoring status and active searches via simple commands.

## Getting Started

### Prerequisites
- Python 3.8+
- Chrome/Chromium & ChromeDriver (for Selenium)

### Installation

1.  **Install Dependencies**
    ```bash
    cd telegram-flight-bot
    pip install -r requirements.txt
    ```

2.  **Configuration**
    Create a `config.env` file in the `telegram-flight-bot` directory:
    ```env
    TELEGRAM_BOT_TOKEN=your_telegram_bot_token
    FLIGHT_SEARCH_INTERVAL=5400
    ```

3.  **Set Flight Preferences**
    *Currently, flight routes and dates are configured in `src/bot.py`. Update the `FLIGHT_CONFIG` dictionary with your desired trips.*

## Usage

Start the bot:
```bash
python telegram-flight-bot/src/bot.py
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
