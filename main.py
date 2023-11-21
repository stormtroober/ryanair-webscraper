import csv
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from datetime import datetime
import argparse
from FlightSearcher import FlightSearcher
    


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Flight Searcher")
    # Add command-line arguments for vpn and saveCsv
    parser.add_argument("--vpn", action="store_true", help="Enable VPN (default is False)")
    parser.add_argument("--saveCsv", action="store_true", help="Save CSV (default is False)")
    parser.add_argument("--debug", action="store_true", help="Debug Mode")
    args = parser.parse_args()

    flight_searcher = FlightSearcher(vpn=args.vpn, saveCsv=args.saveCsv)

    if args.debug:
        dates = ['2024-01-13']
    else:
        dates = ['2024-01-08', '2024-01-13', '2024-01-15', '2024-01-20', '2024-01-22', '2024-01-27', '2024-01-29']

    flights = [{'Origin': 'FRL', 'Destination': 'KTW'}, 
                {'Origin': 'KTW', 'Destination': 'FRL'},
                {'Origin': 'BLQ', 'Destination': 'KRK'},
                {'Origin': 'KRK', 'Destination': 'BLQ'}]
    
    for flight in flights:
        flight_searcher.search_flights_with_retry(flight['Origin'], flight['Destination'], dates, max_retries=5)

    flight_searcher.close()
