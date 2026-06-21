import os
import json # <-- Aggiunta importazione per leggere il file testuale
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv
from pathlib import Path

from PriceTracker import PriceTracker
from MessageFormatter import MessageFormatter
from FlightSearcher import FlightSearcher

# 1. Inizializzo subito il logger
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
logging.getLogger('httpx').setLevel(logging.WARNING)

# 2. Calcolo il path base
BASE_DIR = Path(__file__).resolve().parent
env_path = BASE_DIR / '.env'
config_path = BASE_DIR / 'flights.json' # <-- Nuovo path per il file di configurazione

logger.info(f"Cerco il file .env in: {env_path}")

if env_path.exists():
    logger.info("✅ File .env trovato con successo!")
else:
    logger.error("❌ ATTENZIONE: File .env NON trovato in quel percorso!")
load_dotenv(env_path)

# 3. Funzione per caricare la configurazione esterna
def load_flight_config():
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                logger.info("✅ File flights.json caricato con successo!")
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"❌ Errore di formattazione nel file flights.json: {e}")
    else:
        logger.error("❌ ATTENZIONE: File flights.json NON trovato!")
    
    # Ritorno un fallback vuoto in caso di errore per evitare crash
    return {'flights': []}

# Caricamento della configurazione
FLIGHT_CONFIG = load_flight_config()

flight_searcher = None
search_job = None
price_tracker = PriceTracker()
formatter = MessageFormatter(FLIGHT_CONFIG)
search_counter = 0

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        'Hi! I\'m your flight search bot. Use /start_search to begin monitoring flights.'
    )

async def start_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global flight_searcher, search_job, search_counter, price_tracker

    try:
        if not context.job_queue:
            await update.message.reply_text('Error: Job queue not available. Please restart the bot.')
            return

        price_tracker.reset()
        search_counter = 0

        # Inizializzazione pulita senza VPN
        flight_searcher = FlightSearcher()

        if search_job:
            search_job.schedule_removal()

        search_interval = int(os.getenv("FLIGHT_SEARCH_INTERVAL", 5400))
        search_job = context.job_queue.run_repeating(
            flight_search_job,
            interval=search_interval,
            first=10,
            chat_id=update.effective_chat.id
        )

        await update.message.reply_text(
            formatter.format_search_started(search_interval, FLIGHT_CONFIG['flights'])
        )
        logger.info("Flight search scheduler started")

    except Exception as e:
        logger.error(f"Error starting flight search: {e}")
        await update.message.reply_text(f'Error starting flight search: {e}')

async def stop_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global search_job, flight_searcher, search_counter, price_tracker

    if search_job:
        search_job.schedule_removal()
        search_job = None
        logger.info("Flight search scheduler stopped")

    if flight_searcher:
        flight_searcher.close()
        flight_searcher = None

    price_tracker.reset()
    search_counter = 0

    await update.message.reply_text('Flight search stopped!')

async def flight_search_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    global flight_searcher, search_counter, price_tracker

    try:
        search_counter += 1
        logger.info(f"Starting flight search... (Cycle {search_counter})")

        all_flight_data = {}

        for flight in FLIGHT_CONFIG['flights']:
            flight_data = flight_searcher.search_flights_with_retry(
                flight['Origin'],
                flight['Destination'],
                flight.get('dates', []),
                max_retries=3
            )
            for key, data in flight_data.items():
                data['origin'] = flight['Origin']
                data['destination'] = flight['Destination']
            all_flight_data.update(flight_data)

        if all_flight_data and hasattr(context, 'job') and context.job:
            chat_id = context.job.chat_id
            price_drops, new_flights = price_tracker.check_price_changes(all_flight_data)

            should_send_update = False
            message = ""

            if not price_tracker.first_search_done:
                should_send_update = True
                message = formatter.format_initial_results(all_flight_data)
                price_tracker.first_search_done = True
            elif price_drops:
                should_send_update = True
                message = formatter.format_price_drop(price_drops)

            if should_send_update:
                await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')

        elif hasattr(context, 'job') and context.job:
            chat_id = context.job.chat_id
            await context.bot.send_message(chat_id=chat_id, text=formatter.format_no_flights(FLIGHT_CONFIG['flights']))

        logger.info(f"Flight search completed successfully (Cycle {search_counter})")

    except Exception as e:
        logger.error(f"Error in flight search job: {e}")
        if hasattr(context, 'job') and context.job:
            chat_id = context.job.chat_id
            await context.bot.send_message(chat_id=chat_id, text=formatter.format_error(e, search_counter, FLIGHT_CONFIG))

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global search_job, flight_searcher, search_counter, price_tracker
    status_text = formatter.format_status(search_job, flight_searcher, search_counter, price_tracker, FLIGHT_CONFIG)
    await update.message.reply_text(status_text, parse_mode='Markdown')

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling an update:", exc_info=context.error)

def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
    
    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("start_search", start_search))
    application.add_handler(CommandHandler("stop_search", stop_search))
    application.add_handler(CommandHandler("status", status))
    application.add_error_handler(error_handler)

    print("Bot started. Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()