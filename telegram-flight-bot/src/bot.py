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

# Flight configuration - Update these to match your needs
FLIGHT_CONFIG = {
    'dates': ['2025-07-17', '2025-07-18', '2025-07-19', '2025-07-20', '2025-07-21'],
    'flights': [
        {'Origin': 'AOI', 'Destination': 'KRK'},
        {'Origin': 'RMI', 'Destination': 'KRK'},
    ]
}

# Airport code to city name mapping
AIRPORT_NAMES = {
    'AOI': 'Ancona',
    'RMI': 'Rimini', 
    'KRK': 'Krakow',
    'BGY': 'Bergamo',
    'MXP': 'Milan Malpensa',
    'FCO': 'Rome Fiumicino',
    'NAP': 'Naples',
    'BLQ': 'Bologna',
    'VCE': 'Venice',
    'WAW': 'Warsaw',
    'GDN': 'Gdansk',
    'WRO': 'Wroclaw',
    'POZ': 'Poznan'
}

def get_airport_display_name(code):
    """Get display name for airport code."""
    return AIRPORT_NAMES.get(code, code)

def get_route_display_name(origin, destination):
    """Get human-readable route name."""
    origin_name = get_airport_display_name(origin)
    dest_name = get_airport_display_name(destination)
    return f"{origin} → {destination} ({origin_name} to {dest_name})"

def get_date_range_display():
    """Get human-readable date range."""
    dates = FLIGHT_CONFIG['dates']
    if len(dates) == 1:
        return dates[0]
    elif len(dates) > 1:
        return f"{dates[0]} to {dates[-1]}"
    return "No dates configured"

# Global variables
flight_searcher = None
search_job = None
price_history = {}  # Store price history for each route-date combination
search_counter = 0  # Counter for cycles
first_search_done = False  # Track if first search was completed

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    await update.message.reply_text(
        'Hi! I\'m your flight search bot. Use /start_search to begin monitoring flights every 90 minutes.'
    )

async def start_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start the flight search scheduler."""
    global flight_searcher, search_job, price_history, search_counter, first_search_done
    
    try:
        # Check if job queue is available
        if not context.job_queue:
            await update.message.reply_text(
                'Error: Job queue not available. Please restart the bot.'
            )
            return
            
        # Reset tracking variables
        price_history = {}
        search_counter = 0
        first_search_done = False
            
        # Initialize flight searcher without CSV saving
        flight_searcher = FlightSearcher(vpn=False, saveCsv=False)
        
        # Remove existing job if any
        if search_job:
            search_job.schedule_removal()
        
        # Schedule the flight search job
        search_interval = int(os.getenv("FLIGHT_SEARCH_INTERVAL", 3600))  # 90 minutes default
        search_job = context.job_queue.run_repeating(
            flight_search_job, 
            interval=search_interval, 
            first=10,  # Start after 10 seconds
            chat_id=update.effective_chat.id
        )
        
        # Build dynamic route list for message
        route_list = ""
        for flight in FLIGHT_CONFIG['flights']:
            route_display = get_route_display_name(flight['Origin'], flight['Destination'])
            route_list += f"• {route_display}\n"
        
        await update.message.reply_text(
            f'Flight search started! I will search for flights every {search_interval // 60} minutes.\n\n'
            f'🛫 Searching flights:\n{route_list}\n'
            f'📅 Dates: {get_date_range_display()}\n\n'
            f'📊 Price tracking enabled:\n'
            f'• First search results will always be shown\n'
            f'• You\'ll be notified when prices drop below previous minimums'
        )
        
        logger.info("Flight search scheduler started")
        
    except Exception as e:
        logger.error(f"Error starting flight search: {e}")
        await update.message.reply_text(f'Error starting flight search: {e}')

async def stop_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Stop the flight search scheduler."""
    global search_job, flight_searcher, price_history, search_counter, first_search_done
    
    if search_job:
        search_job.schedule_removal()
        search_job = None
        logger.info("Flight search scheduler stopped")
        
    if flight_searcher:
        flight_searcher.close()
        flight_searcher = None
    
    # Reset tracking variables
    price_history = {}
    search_counter = 0
    first_search_done = False
        
    await update.message.reply_text('Flight search stopped!')

def check_price_changes(all_flight_data):
    """Check for price changes and detect local minimums."""
    global price_history, first_search_done
    
    price_drops = {}
    new_flights = {}
    
    for flight_key, flight_info in all_flight_data.items():
        current_price = flight_info['amount']
        
        # If this is the first time we see this flight or it's the first search
        if flight_key not in price_history or not first_search_done:
            price_history[flight_key] = {
                'min_price': current_price,
                'last_price': current_price,
                'currency': flight_info['currency'],
                'date': flight_info['date'],
                'origin': flight_info.get('origin', ''),
                'destination': flight_info.get('destination', ''),
                'route': flight_info.get('route', 'Unknown route')
            }
            new_flights[flight_key] = flight_info
        else:
            # Check if current price is lower than the recorded minimum
            if current_price < price_history[flight_key]['min_price']:
                old_min = price_history[flight_key]['min_price']
                price_history[flight_key]['min_price'] = current_price
                price_drops[flight_key] = {
                    'current_price': current_price,
                    'previous_min': old_min,
                    'currency': flight_info['currency'],
                    'date': flight_info['date'],
                    'origin': flight_info.get('origin', ''),
                    'destination': flight_info.get('destination', ''),
                    'route': flight_info.get('route', 'Unknown route')
                }
            
            # Update last price
            price_history[flight_key]['last_price'] = current_price
    
    return price_drops, new_flights

def group_flights_by_route(flight_data):
    """Group flight data by route."""
    routes = {}
    for flight_key, flight_info in flight_data.items():
        origin = flight_info.get('origin', '')
        destination = flight_info.get('destination', '')
        route_key = f"{origin}_{destination}"
        if route_key not in routes:
            routes[route_key] = {
                'origin': origin,
                'destination': destination,
                'flights': {}
            }
        routes[route_key]['flights'][flight_key] = flight_info
    return routes

async def flight_search_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """The actual flight search job that runs periodically."""
    global flight_searcher, search_counter, first_search_done
    
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
            # Add origin and destination to each flight data entry
            for key, data in flight_data.items():
                data['origin'] = flight['Origin']
                data['destination'] = flight['Destination']
            all_flight_data.update(flight_data)
        
        if all_flight_data and hasattr(context, 'job') and context.job:
            chat_id = context.job.chat_id
            
            # Check for price changes
            price_drops, new_flights = check_price_changes(all_flight_data)
            
            # Determine what to send
            should_send_update = False
            message = ""
            
            # First search - always send
            if not first_search_done:
                should_send_update = True
                message = f"🚀 *Initial Flight Search Results - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
                
                # Group flights by route for display
                routes = group_flights_by_route(all_flight_data)
                
                for route_key, route_data in routes.items():
                    origin = route_data['origin']
                    destination = route_data['destination']
                    route_display = get_route_display_name(origin, destination)
                    
                    message += f"🛫 *{route_display}*\n"
                    for flight_key, flight_info in route_data['flights'].items():
                        date = flight_info['date']
                        price = flight_info['amount']
                        currency = flight_info['currency']
                        message += f"📅 {date}: {currency}{price:.2f}\n"
                    message += "\n"
                
                first_search_done = True
            
            # Price drops detected
            elif price_drops:
                should_send_update = True
                message = f"📉 *Price Drop Alert! - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
                
                # Group price drops by route
                drop_routes = group_flights_by_route(price_drops)
                
                for route_key, route_data in drop_routes.items():
                    origin = route_data['origin']
                    destination = route_data['destination']
                    route_display = get_route_display_name(origin, destination)
                    
                    message += f"🛫 *{route_display}* (New lowest prices!)\n"
                    for flight_key, drop_info in route_data['flights'].items():
                        date = drop_info['date']
                        current_price = drop_info['current_price']
                        previous_min = drop_info['previous_min']
                        currency = drop_info['currency']
                        savings = previous_min - current_price
                        message += f"📅 {date}: {currency}{current_price:.2f} 🔻 (was {currency}{previous_min:.2f}, saved {currency}{savings:.2f})\n"
                    message += "\n"
            
            # Send message if needed
            if should_send_update:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode='Markdown'
                )
        
        elif hasattr(context, 'job') and context.job:
            # Send notification if no flights found
            chat_id = context.job.chat_id
            
            # Build route list for error message
            route_list = ", ".join([f"{flight['Origin']}→{flight['Destination']}" for flight in flights])
            
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"⚠️ No flights found at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Cycle {search_counter})\n"
                     f"Searched routes: {route_list} for dates {get_date_range_display()}"
            )
        
        logger.info(f"Flight search completed successfully (Cycle {search_counter})")
        
    except Exception as e:
        logger.error(f"Error in flight search job: {e}")
        if hasattr(context, 'job') and context.job:
            chat_id = context.job.chat_id
            
            # Build route list for error message
            route_list = ", ".join([f"{flight['Origin']}→{flight['Destination']}" for flight in FLIGHT_CONFIG['flights']])
            
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"❌ Flight search failed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Cycle {search_counter})\n"
                     f"Error: {e}\n"
                     f"Routes: {route_list}"
            )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the current status of the flight search."""
    global search_job, flight_searcher, search_counter, price_history, first_search_done
    
    if search_job and flight_searcher:
        next_run = search_job.next_t
        
        # Build configured routes list
        route_list = "\n".join([f"• {get_route_display_name(flight['Origin'], flight['Destination'])}" 
                               for flight in FLIGHT_CONFIG['flights']])
        
        status_text = (
            f"🟢 Flight search is ACTIVE\n"
            f"Next search: {next_run.strftime('%Y-%m-%d %H:%M:%S') if next_run else 'Unknown'}\n"
            f"Interval: {int(os.getenv('FLIGHT_SEARCH_INTERVAL', 3600)) // 60} minutes\n"
            f"Search cycles completed: {search_counter}\n"
            f"First search done: {'✅' if first_search_done else '❌'}\n"
            f"Flights being tracked: {len(price_history)}\n\n"
            f"🛫 Configured routes:\n{route_list}\n"
            f"📅 Dates: {get_date_range_display()}"
        )
        
        if price_history:
            status_text += "\n\n📊 Current minimum prices:\n"
            # Group by route for better display
            route_prices = {}
            for flight_key, history in price_history.items():
                origin = history.get('origin', 'Unknown')
                destination = history.get('destination', 'Unknown')
                route_display = get_route_display_name(origin, destination)
                
                if route_display not in route_prices:
                    route_prices[route_display] = []
                
                route_prices[route_display].append({
                    'date': history['date'],
                    'min_price': history['min_price'],
                    'last_price': history['last_price'],
                    'currency': history['currency']
                })
            
            for route_display, flights in route_prices.items():
                status_text += f"\n*{route_display}*\n"
                for flight in flights:
                    date = flight['date']
                    min_price = flight['min_price']
                    last_price = flight['last_price']
                    currency = flight['currency']
                    
                    trend = "🟢" if last_price == min_price else "🔺"
                    status_text += f"📅 {date}: {currency}{min_price:.2f} (Last: {currency}{last_price:.2f}) {trend}\n"
    else:
        status_text = "🔴 Flight search is INACTIVE"
    
    await update.message.reply_text(status_text, parse_mode='Markdown')

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