class PriceTracker:
    def __init__(self):
        self.price_history = {}
        self.first_search_done = False

    def check_price_changes(self, all_flight_data):
        price_drops = {}
        new_flights = {}

        for flight_key, flight_info in all_flight_data.items():
            current_price = flight_info['amount']

            if flight_key not in self.price_history or not self.first_search_done:
                self.price_history[flight_key] = {
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
                if current_price < self.price_history[flight_key]['min_price']:
                    old_min = self.price_history[flight_key]['min_price']
                    self.price_history[flight_key]['min_price'] = current_price
                    price_drops[flight_key] = {
                        'current_price': current_price,
                        'previous_min': old_min,
                        'currency': flight_info['currency'],
                        'date': flight_info['date'],
                        'origin': flight_info.get('origin', ''),
                        'destination': flight_info.get('destination', ''),
                        'route': flight_info.get('route', 'Unknown route')
                    }
                self.price_history[flight_key]['last_price'] = current_price

        return price_drops, new_flights

    def reset(self):
        self.price_history = {}
        self.first_search_done = False