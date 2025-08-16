import os
import asyncio
import logging
from datetime import datetime, timedelta
from telegram import InputFile
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv
from PriceTracker import PriceTracker
from MessageFormatter import MessageFormatter

import sys
sys.path.append('/home/aless/Documents/ryanair-webscraper')
from FlightSearcher import FlightSearcher

# Load environment variables
load_dotenv('/home/aless/Documents/ryanair-webscraper/telegram-flight-bot/config.env')

# Configure logging - disable httpx and telegram logs
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.WARNING
)
# Disable specific loggers
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('telegram').setLevel(logging.WARNING)
logging.getLogger('telegram.ext').setLevel(logging.WARNING)

# Only show our bot logs
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Flight configuration - Update these to match your needs
FLIGHT_CONFIG = {
    'dates': ['2025-08-22', '2025-08-23', '2025-08-24', '2025-08-25', '2025-08-29',
              '2025-08-30', '2025-08-31', '2025-09-01', '2025-09-05', '2025-09-06', '2025-09-07'],
    'flights': [
        {'Origin': 'AOI', 'Destination': 'KRK'},
    ]
}
# FLIGHT_CONFIG = {
#     'dates': ['2025-08-22'],
#     'flights': [
#         {'Origin': 'BLQ', 'Destination': 'KRK'},
#     ]
# }

# Global variables
flight_searcher = None
search_job = None
price_tracker = PriceTracker()
formatter = MessageFormatter(FLIGHT_CONFIG)
# Initialize flight searcher without CSV saving
flight_searcher = FlightSearcher(vpn=True, save=True)
search_counter = 0

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    await update.message.reply_text(
        'Hi! I\'m your flight search bot. Use /start_search to begin monitoring flights every 90 minutes.'
    )

async def start_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start the flight search scheduler."""
    global flight_searcher, search_job, search_counter, price_tracker

    try:
        if not context.job_queue:
            await update.message.reply_text(
                'Error: Job queue not available. Please restart the bot.'
            )
            return

        # Reset tracking variables
        price_tracker.reset()
        search_counter = 0

        

        # Remove existing job if any
        if search_job:
            search_job.schedule_removal()

        # Schedule the flight search job
        search_interval = int(os.getenv("FLIGHT_SEARCH_SAVE_INTERVAL", 21600))  # 6 hours default
        search_job = context.job_queue.run_repeating(
            flight_search_job,
            interval=search_interval,
            first=10,
            chat_id=update.effective_chat.id
        )

        await update.message.reply_text(
            formatter.format_search_started(
                search_interval,
                FLIGHT_CONFIG['flights'],
                formatter.get_route_display_name,
                formatter.get_date_range_display
            )
        )
        logger.info("Flight search scheduler started")

    except Exception as e:
        logger.error(f"Error starting flight search: {e}")
        await update.message.reply_text(f'Error starting flight search: {e}')

async def stop_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Stop the flight search scheduler."""
    global search_job, flight_searcher, search_counter, price_tracker

    if search_job:
        search_job.schedule_removal()
        search_job = None
        logger.info("Flight search scheduler stopped")

    if flight_searcher:
        flight_searcher.close()
        flight_searcher = None

    # Reset tracking variables
    price_tracker.reset()
    search_counter = 0

    await update.message.reply_text('Flight search stopped!')

async def flight_search_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    global flight_searcher, search_counter, price_tracker

    try:
        search_counter += 1
        logger.info(f"Starting flight search... (Cycle {search_counter})")

        dates = FLIGHT_CONFIG['dates']
        flights = FLIGHT_CONFIG['flights']

        all_flight_data = {}

        for flight in flights:
            flight_data = flight_searcher.search_flights_with_retry(
                flight['Origin'],
                flight['Destination'],
                dates,
                max_retries=3
            )
            for key, data in flight_data.items():
                data['origin'] = flight['Origin']
                data['destination'] = flight['Destination']
            all_flight_data.update(flight_data)

        # Send a confirmation message every 2 cycles
        if hasattr(context, 'job') and context.job and search_counter % 2 == 0:
            chat_id = context.job.chat_id
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"✅ Il bot sta funzionando correttamente! (Ciclo {search_counter})",
                parse_mode='Markdown'
            )

        # Send the JSON file every 4 cycles
        if hasattr(context, 'job') and context.job and search_counter % 4 == 0:
            chat_id = context.job.chat_id
            saver = get_flight_saver()
            json_file = saver.export_json()
            with open(json_file, "rb") as f:
                await context.bot.send_document(
                    chat_id=chat_id,
                    document=InputFile(f, filename=json_file),
                    caption=f"📄 Export voli (Ciclo {search_counter})"
                )

        logger.info(f"Flight search completed successfully (Cycle {search_counter})")

    except Exception as e:
        logger.error(f"Error in flight search job: {e}")
        if hasattr(context, 'job') and context.job:
            chat_id = context.job.chat_id
            await context.bot.send_message(
                chat_id=chat_id,
                text=formatter.format_error(e, search_counter, FLIGHT_CONFIG)
            )

async def db_summary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    saver = get_flight_saver()
    summary = saver.get_summary()
    await update.message.reply_text(summary)
    # Esporta e invia il file JSON
    json_file = saver.export_json()
    with open(json_file, "rb") as f:
        await update.message.reply_document(document=InputFile(f, filename=json_file))

def get_flight_saver():
    global flight_searcher
    if flight_searcher is not None:
        return flight_searcher.get_saver()

import traceback

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    # Invia un messaggio all'utente se possibile
    if update and hasattr(update, "message") and update.message:
        await update.message.reply_text("❌ Si è verificato un errore interno. Riprova più tardi.")
    # Logga lo stack trace completo
    tb = "".join(traceback.format_exception(None, context.error, context.error.__traceback__))
    logger.error(tb)

def main() -> None:
    """Start the bot."""
    token = os.getenv("TELEGRAM_NEW_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_NEW_BOT_TOKEN not found in environment variables")
    
    # Create the Application with job queue enabled
    application = Application.builder().token(token).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("start_search", start_search))
    application.add_handler(CommandHandler("stop_search", stop_search))
    #application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("db_summary", db_summary))

    application.add_error_handler(error_handler)

    # Run the bot until the user presses Ctrl-C
    print("Bot started. Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()