class FlightSearch:
    def __init__(self, origin, destination, dates):
        self.origin = origin
        self.destination = destination
        self.dates = dates
        self.results = []

    def search_flights(self):
        # Implement the logic to search for flights based on the parameters
        pass

    def get_results(self):
        return self.results

    def clear_results(self):
        self.results = []