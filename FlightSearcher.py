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
from config import flights_csv_path
from config import bash_script_connect
from config import bash_script_disconnect
from config import vpn_countries

class FlightSearcher:
    def __init__(self, vpn, saveCsv):
        self.vpn = vpn
        self.saveCsv = saveCsv

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
                return True
            else:
                print("Failed to connect to NordVPN.")
                return False

    def __search_flights(self, origins, destinations, dates):
        prices = {}
        for origin in origins:
            for destination in destinations:
                for date in dates:
                    flight_key = f"{origin}-{destination} on {date}"
                    prices[flight_key] = self.__get_price(origin, destination, date)
        return prices, flight_key
    
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
                EC.element_to_be_clickable((By.CLASS_NAME, 'cookie-popup-with-overlay__button'))
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
        self.driver.quit()
        self.__disconnect_vpn()

    def __search_and_save_flights(self, origins, destinations, dates):
        found = False
        #If the vpn is on, i connect everytime to a different one from the configs
        if self.vpn:
            self.__connect_vpn(random.choice(vpn_countries))
        flight_prices, flight_key  = self.__search_flights(origins, destinations, dates)
        print(flight_prices)
        if 'currency' not in flight_prices[flight_key]:
            return found
        else:
            found = True
        if self.saveCsv:
            print("Saving flights data...")
            #I save the flight in a csv
            with open(flights_csv_path, 'a', newline='') as file:
                writer = csv.writer(file)
                for key, value in flight_prices.items():
                    if not value == "Flight not found":
                        origin_destination = key.split(' on ')[0]
                        flight_date = value['date']
                        price_currency = f"{value['amount']}{value['currency']}"
                        today_date = datetime.today().strftime("%Y-%m-%d %H:%M")

                        writer.writerow([origin_destination, flight_date, price_currency, today_date])
        return found
        
    def search_flights_with_retry(self, origin, destination, dates, max_retries):
        """
        Searches for flights based on the provided origins, destinations, and dates.

        This private method represents the core functionality for searching flights.
        It should be implemented with the actual logic for searching flights using 
        external APIs or data sources. The method should save the search results and 
        return a boolean indicating the success or failure of the flight search.

        Parameters:
        - origins (list): A list of origin locations.
        - destinations (list): A list of destination locations.
        - dates (list): A list of dates for the flight search.

        Returns:
        - bool: True if flights are found, False otherwise.
        """
        for attempt in range(max_retries):
            found = self.__search_and_save_flights([origin], [destination], dates)
            if found:
                return True
            time.sleep(5)
            print(f"Attempt {attempt + 1} failed. Retrying...")
        print('All Attempts failed.')
        return False