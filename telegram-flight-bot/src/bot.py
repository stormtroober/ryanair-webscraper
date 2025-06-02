import os
import asyncio
import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv
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

# Global variables
flight_searcher = None
search_job = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    await update.message.reply_text(
        'Hi! I\'m your flight search bot. Use /start_search to begin monitoring flights every 90 minutes.'
    )

async def start_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start the flight search scheduler."""
    global flight_searcher, search_job
    
    try:
        # Check if job queue is available
        if not context.job_queue:
            await update.message.reply_text(
                'Error: Job queue not available. Please restart the bot.'
            )
            return
            
        # Initialize flight searcher without CSV saving
        flight_searcher = FlightSearcher(vpn=False, saveCsv=False)
        
        # Remove existing job if any
        if search_job:
            search_job.schedule_removal()
        
        # Schedule the flight search job
        search_interval = int(os.getenv("FLIGHT_SEARCH_INTERVAL", 5400))  # 90 minutes default
        search_job = context.job_queue.run_repeating(
            flight_search_job, 
            interval=search_interval, 
            first=10,  # Start after 10 seconds
            chat_id=update.effective_chat.id
        )
        
        await update.message.reply_text(
            f'Flight search started! I will search for flights every {search_interval // 60} minutes.\n'
            f'Searching flights from AOI to KRK for dates: 2025-07-18 to 2025-07-21'
        )
        
        logger.info("Flight search scheduler started")
        
    except Exception as e:
        logger.error(f"Error starting flight search: {e}")
        await update.message.reply_text(f'Error starting flight search: {e}')

async def stop_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Stop the flight search scheduler."""
    global search_job, flight_searcher
    
    if search_job:
        search_job.schedule_removal()
        search_job = None
        logger.info("Flight search scheduler stopped")
        
    if flight_searcher:
        flight_searcher.close()
        flight_searcher = None
        
    await update.message.reply_text('Flight search stopped!')

async def flight_search_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """The actual flight search job that runs periodically."""
    global flight_searcher
    
    try:
        logger.info("Starting flight search...")
        
        dates = ['2025-07-18', '2025-07-19', '2025-07-20', '2025-07-21']
        flights = [{'Origin': 'AOI', 'Destination': 'KRK'}]
        
        all_flight_data = {}
        
        for flight in flights:
            flight_data = flight_searcher.search_flights_with_retry(
                flight['Origin'], 
                flight['Destination'], 
                dates, 
                max_retries=3
            )
            all_flight_data.update(flight_data)
        
        # Format and send flight prices via Telegram
        if all_flight_data and hasattr(context, 'job') and context.job:
            chat_id = context.job.chat_id
            
            message = f"✈️ *Flight Prices Update - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
            message += "🛫 *AOI → KRK*\n"
            
            for flight_key, flight_info in all_flight_data.items():
                date = flight_info['date']
                price = flight_info['amount']
                currency = flight_info['currency']
                message += f"📅 {date}: {currency}{price:.2f}\n"
            
            await context.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='Markdown'
            )
        elif hasattr(context, 'job') and context.job:
            # Send notification even if no flights found
            chat_id = context.job.chat_id
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"⚠️ No flights found at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
        
        logger.info("Flight search completed successfully")
        
    except Exception as e:
        logger.error(f"Error in flight search job: {e}")
        if hasattr(context, 'job') and context.job:
            chat_id = context.job.chat_id
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"❌ Flight search failed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                     f"Error: {e}"
            )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the current status of the flight search."""
    global search_job, flight_searcher
    
    if search_job and flight_searcher:
        next_run = search_job.next_t
        status_text = (
            f"🟢 Flight search is ACTIVE\n"
            f"Next search: {next_run.strftime('%Y-%m-%d %H:%M:%S') if next_run else 'Unknown'}\n"
            f"Interval: {int(os.getenv('FLIGHT_SEARCH_INTERVAL', 5400)) // 60} minutes"
        )
    else:
        status_text = "🔴 Flight search is INACTIVE"
    
    await update.message.reply_text(status_text)

def main() -> None:
    """Start the bot."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
    
    # Create the Application with job queue enabled
    application = Application.builder().token(token).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("start_search", start_search))
    application.add_handler(CommandHandler("stop_search", stop_search))
    application.add_handler(CommandHandler("status", status))

    # Run the bot until the user presses Ctrl-C
    print("Bot started. Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()