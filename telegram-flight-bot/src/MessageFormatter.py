import os
from datetime import datetime

class MessageFormatter:
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

    def __init__(self, flight_config):
        self.flight_config = flight_config

    def get_airport_display_name(self, code):
        return self.AIRPORT_NAMES.get(code, code)

    def get_route_display_name(self, origin, destination):
        origin_name = self.get_airport_display_name(origin)
        dest_name = self.get_airport_display_name(destination)
        return f"{origin} → {destination} ({origin_name} to {dest_name})"

    def get_date_range_display(self):
        dates = self.flight_config['dates']
        if len(dates) == 1:
            return dates[0]
        elif len(dates) > 1:
            return f"{dates[0]} to {dates[-1]}"
        return "No dates configured"

    def format_initial_results(self, all_flight_data):
        message = f"🚀 *Initial Flight Search Results - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
        routes = self.group_flights_by_route(all_flight_data)
        for route_key, route_data in routes.items():
            origin = route_data['origin']
            destination = route_data['destination']
            route_display = self.get_route_display_name(origin, destination)
            message += f"🛫 *{route_display}*\n"
            for flight_key, flight_info in route_data['flights'].items():
                date = flight_info['date']
                price = flight_info['amount']
                currency = flight_info['currency']
                message += f"📅 {date}: {currency}{price:.2f}\n"
            message += "\n"
        return message

    def format_price_drop(self, price_drops):
        message = f"📉 *Price Drop Alert! - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
        drop_routes = self.group_flights_by_route(price_drops)
        for route_key, route_data in drop_routes.items():
            origin = route_data['origin']
            destination = route_data['destination']
            route_display = self.get_route_display_name(origin, destination)
            message += f"🛫 *{route_display}* (New lowest prices!)\n"
            for flight_key, drop_info in route_data['flights'].items():
                date = drop_info['date']
                current_price = drop_info['current_price']
                previous_min = drop_info['previous_min']
                currency = drop_info['currency']
                savings = previous_min - current_price
                message += f"📅 {date}: {currency}{current_price:.2f} 🔻 (was {currency}{previous_min:.2f}, saved {currency}{savings:.2f})\n"
            message += "\n"
        return message

    def format_no_flights(self, flights):
        route_list = ", ".join([f"{flight['Origin']}→{flight['Destination']}" for flight in flights])
        return (
            f"⚠️ No flights found at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Searched routes: {route_list} for dates {self.get_date_range_display()}"
        )

    def group_flights_by_route(self, flight_data):
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
    

    def format_status(self, search_job, flight_searcher, search_counter, price_tracker, FLIGHT_CONFIG):
        if search_job and flight_searcher:
            next_run = getattr(search_job, 'next_t', None)
            route_list = "\n".join([
                f"• {self.get_route_display_name(flight['Origin'], flight['Destination'])}"
                for flight in FLIGHT_CONFIG['flights']
            ])
            status_text = (
                f"🟢 Flight search is ACTIVE\n"
                f"Next search: {next_run.strftime('%Y-%m-%d %H:%M:%S') if next_run else 'Unknown'}\n"
                f"Interval: {int(os.getenv('FLIGHT_SEARCH_INTERVAL', 3600)) // 60} minutes\n"
                f"Search cycles completed: {search_counter}\n"
                f"First search done: {'✅' if price_tracker.first_search_done else '❌'}\n"
                f"Flights being tracked: {len(price_tracker.price_history)}\n\n"
                f"🛫 Configured routes:\n{route_list}\n"
                f"📅 Dates: {self.get_date_range_display()}"
            )
            if price_tracker.price_history:
                status_text += "\n\n📊 Current minimum prices:\n"
                route_prices = {}
                for flight_key, history in price_tracker.price_history.items():
                    origin = history.get('origin', 'Unknown')
                    destination = history.get('destination', 'Unknown')
                    route_display = self.get_route_display_name(origin, destination)
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
        return status_text
    
    def format_error(self, error, search_counter, FLIGHT_CONFIG):
        route_list = ", ".join([
            f"{flight['Origin']}→{flight['Destination']}"
            for flight in FLIGHT_CONFIG['flights']
        ])
        return (
            f"❌ Flight search failed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Cycle {search_counter})\n"
            f"Error: {error}\n"
            f"Routes: {route_list}"
        )
    
    def format_search_started(self, search_interval, flights, get_route_display_name, get_date_range_display):
        route_list = ""
        for flight in flights:
            route_display = get_route_display_name(flight['Origin'], flight['Destination'])
            route_list += f"• {route_display}\n"
        return (
            f'Flight search started! I will search for flights every {search_interval // 60} minutes.\n\n'
            f'🛫 Searching flights:\n{route_list}\n'
            f'📅 Dates: {get_date_range_display()}\n\n'
            f'📊 Price tracking enabled:\n'
            f'• First search results will always be shown\n'
            f'• You\'ll be notified when prices drop below previous minimums'
        )