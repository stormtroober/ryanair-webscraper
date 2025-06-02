# Telegram Flight Bot

This project is a Telegram bot that initiates flight searches every 90 minutes when a button is pressed. It utilizes the `python-telegram-bot` library to interact with the Telegram API and manage user commands.

## Features

- Start a flight search with a button press.
- Automatically schedule flight searches every 90 minutes.
- User-friendly interaction through Telegram commands.

## Project Structure

```
telegram-flight-bot
├── src
│   ├── bot.py                # Initializes the Telegram bot and command handlers
│   ├── handlers              # Contains command handlers for the bot
│   │   ├── __init__.py
│   │   ├── start_handler.py   # Handles the /start command
│   │   └── flight_handler.py   # Initiates flight search
│   ├── services              # Contains business logic and scheduling services
│   │   ├── __init__.py
│   │   ├── flight_service.py   # Contains methods for searching flights
│   │   └── scheduler_service.py # Manages scheduling of tasks
│   ├── models                # Contains data models
│   │   ├── __init__.py
│   │   └── flight_search.py    # Represents flight search parameters and results
│   ├── utils                 # Contains utility functions and configurations
│   │   ├── __init__.py
│   │   └── config.py          # Configuration settings
│   └── main.py               # Entry point of the application
├── requirements.txt          # Lists project dependencies
├── config.env                # Contains environment variables
├── .gitignore                # Specifies files to ignore in Git
└── README.md                 # Project documentation
```

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd telegram-flight-bot
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your environment variables in `config.env`:
   ```
   TELEGRAM_BOT_TOKEN=<your-telegram-bot-token>
   ```

## Usage

1. Run the bot:
   ```
   python src/main.py
   ```

2. Interact with the bot on Telegram by sending the `/start` command to initiate the flight search.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.