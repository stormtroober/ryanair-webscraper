
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from datetime import datetime
import subprocess

from FlightURLBuilder import FlightURLBuilder

class FlightSearcher:
    def __init__(self):
        self.driver = webdriver.Chrome()
        self.driver.delete_all_cookies()

    def disconnect_vpn(self):
        bash_script = './nordvpn_disconnect.sh'  # Replace with the actual path
        command = f"{bash_script}"
        result = subprocess.run(command, shell=True)

    def connect_vpn(self, vpn_server):
        bash_script = './nordvpn_connect.sh'  # Replace with the actual path
        command = f"{bash_script} {vpn_server}"
        result = subprocess.run(command, shell=True)

        if result.returncode == 0:
            print("Connected to NordVPN successfully.")
            return True
        else:
            print("Failed to connect to NordVPN.")
            return False

    def search_flights(self, origins, destinations, dates):
        prices = {}
        for origin in origins:
            for destination in destinations:
                for date in dates:
                    flight_key = f"{origin}-{destination} on {date}"
                    prices[flight_key] = self.get_price(origin, destination, date)
        return prices

    def get_price(self, origin, destination, date):
        flightBuilder = FlightURLBuilder()
        flightBuilder.set_origin(origin)
        flightBuilder.set_destination(destination)
        flightBuilder.set_date_out(date)

        url = flightBuilder.build_url()
        self.driver.delete_all_cookies()
        self.driver.get(url)
        self.driver.delete_all_cookies()

        try:
            cookie_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CLASS_NAME, 'cookie-popup-with-overlay__button'))
            )
            cookie_button.click()
        except TimeoutException:
            print("Cookie button not found or not clickable.")

        try:
            
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "flight-card-new"))
            )
            price_carousel = self.driver.find_elements(By.CSS_SELECTOR, "carousel-container carousel-item")
            price_info = self.get_price_selected(price_carousel, datetime.strptime(date, "%Y-%m-%d"))
            return price_info
        except TimeoutException:
            return "Flight not found"

    def get_price_selected(self, priceCarousel, flightDate):
        priceSelected = None
        for box in priceCarousel:
            child_elements = box.find_elements(By.XPATH, "./*")
            for element in child_elements:
                isSelected = 'date-item--selected' in element.get_attribute('class').split()
                if isSelected:
                    priceSelected = box.find_element(By.CSS_SELECTOR, 'ry-price')
                    break
        return self.extract_price_info(priceSelected.text, flightDate)

    def extract_price_info(self, text, flightDate):
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
        self.disconnect_vpn()

def search_and_print_flights(flight_searcher, origins, destinations, dates):
    flight_prices = flight_searcher.search_flights(origins, destinations, dates)
    print(flight_prices)

if __name__ == "__main__":
    flight_searcher = FlightSearcher()

    vpn_connection = False
    if vpn_connection:
        if not flight_searcher.connect_vpn('Germany'):
            print("Exiting due to VPN connection failure.")
            flight_searcher.close()
            exit()

    dates = ['2024-01-08', '2024-01-13', '2024-01-15', '2024-01-20', '2024-01-22', '2024-01-27', '2024-01-29']

    # Search for flights from FRL to KTW
    search_and_print_flights(flight_searcher, ['FRL'], ['KTW'], dates)

    # Search for flights from KTW to FRL
    search_and_print_flights(flight_searcher, ['KTW'], ['FRL'], dates)

    flight_searcher.close()
