import csv
from selenium import webdriver
import subprocess
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import datetime
from FlightURLBuilder import FlightURLBuilder
from selenium.webdriver.common.by import By
from datetime import datetime
import random
import time
from FlightSaver import FlightSaver
from utils.config import flights_csv_path
from utils.config import bash_script_connect
from utils.config import bash_script_disconnect
from utils.config import vpn_countries

class FlightSearcher:
    def __init__(self, vpn, save):
        self.vpn = vpn
        self.save = save
        self.saver = FlightSaver()

    def __disconnect_vpn(self):
        if self.vpn:
            command = f"{bash_script_disconnect}"
            subprocess.run(command, shell=True)

    def __connect_vpn(self, vpn_server):
        if self.vpn:
            command = f"{bash_script_connect} {vpn_server}"
            result = subprocess.run(command, shell=True)

            if result.returncode == 0:
                print("Connected to NordVPN successfully.")
                # Wait for a few seconds to ensure the VPN connection is established
                time.sleep(10)
                return True
            else:
                print("Failed to connect to NordVPN.")
                return False
            
    def get_saver(self):
        return self.saver        

    def __search_flights(self, origins, destinations, dates):
        prices = {}
        for origin in origins:
            for destination in destinations:
                for date in dates:
                    flight_key = f"{origin}-{destination} on {date}"
                    prices[flight_key] = self.__get_price(origin, destination, date)
        return prices
    
    def __setupWebDriver(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless") 
        chrome_options.add_argument("--disable-cache")
        chrome_options.add_argument("--disable-application-cache")
        chrome_options.add_argument("--disable-offline-load-stale-cache")
        self.driver = webdriver.Chrome(chrome_options)
        self.driver.delete_all_cookies()

    def __get_price(self, origin, destination, date):
        flightBuilder = FlightURLBuilder()
        flightBuilder.set_origin(origin)
        flightBuilder.set_destination(destination)
        flightBuilder.set_date_out(date)

        url = flightBuilder.build_url()
        self.__setupWebDriver()
        self.driver.get(url)

        try:
            #Wait for the cookie button to be clickable
            cookie_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CLASS_NAME, 'cookie-popup-with-overlay__button-settings'))
            )
            cookie_button.click()
        except TimeoutException:
            print("Cookie button not found or not clickable.")

        try:
            #Wait for the card of the price to be visible
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "flight-card-new"))
            )
            price_carousel = self.driver.find_elements(By.CSS_SELECTOR, "carousel-container carousel-item")
            price_info = self.__get_price_selected(price_carousel, datetime.strptime(date, "%Y-%m-%d"))

            self.driver.delete_all_cookies()
            self.driver.quit()
            return price_info
        except TimeoutException:
            return "Flight not found"

    def __get_price_selected(self, priceCarousel, flightDate):
        priceSelected = None
        for box in priceCarousel:
            child_elements = box.find_elements(By.XPATH, "./*")
            for element in child_elements:
                isSelected = 'date-item--selected' in element.get_attribute('class').split()
                if isSelected:
                    priceSelected = box.find_element(By.CSS_SELECTOR, 'ry-price')
                    break
        return self.__extract_price_info(priceSelected.text, flightDate)

    def __extract_price_info(self, text, flightDate):
        try:
            parts = text.split()
            currency = parts[0]
            amount_str = ''.join(parts[1:]).replace(',', '.')
            amount = float(amount_str)
            return {
                'currency': currency,
                'amount': amount,
                'date': flightDate.strftime("%Y-%m-%d")
            }
        except Exception as e:
            print(f"Error extracting price info: {e}")
            return None

    def close(self):
        if hasattr(self, 'driver'):
            self.driver.quit()
        self.__disconnect_vpn()

    def __search_and_save_flights(self, origins, destinations, dates):
        #If the vpn is on, i connect everytime to a different one from the configs
        if self.vpn:
            self.__connect_vpn(random.choice(vpn_countries))
        
        flight_prices = self.__search_flights(origins, destinations, dates)
        print(flight_prices)
        
        # Filter out flights not found and save to CSV if needed
        valid_flights = {}
        for key, value in flight_prices.items():
            if value != "Flight not found" and value is not None:
                valid_flights[key] = value

        if self.save and valid_flights:
            print("Saving flights data...")
            print(valid_flights)
            self.saver.save(valid_flights)

        return valid_flights
        
    def search_flights_with_retry(self, origin, destination, dates, max_retries):
        """
        Searches for flights based on the provided origins, destinations, and dates.

        This method represents the core functionality for searching flights.
        It should be implemented with the actual logic for searching flights using 
        external APIs or data sources. The method should save the search results and 
        return the flight data dictionary.

        Parameters:
        - origin (str): Origin location.
        - destination (str): Destination location.
        - dates (list): A list of dates for the flight search.
        - max_retries (int): Maximum number of retry attempts.

        Returns:
        - dict: Dictionary with flight data if flights are found, empty dict otherwise.
        """
        for attempt in range(max_retries):
            flight_data = self.__search_and_save_flights([origin], [destination], dates)
            if flight_data:  # If we found any valid flights
                return flight_data
            time.sleep(5)
            print(f"Attempt {attempt + 1} failed. Retrying...")
        print('All Attempts failed.')
        return {}  # Return empty dict instead of False