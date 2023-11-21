from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from UtilityMethods import get_price_selected
from datetime import datetime
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from FlightURLBuilder import FlightURLBuilder


flightBuilder = FlightURLBuilder()
flightBuilder.set_origin('BLQ')
flightBuilder.set_destination('KRK')

date_object = datetime(2024, 1, 15)
flightBuilder.set_date_out(date_object.strftime("%Y-%m-%d"))

driver = webdriver.Chrome()
print("Retrieving page and deleting cookies...")
driver.delete_all_cookies()
driver.get(flightBuilder.build_url())
driver.delete_all_cookies()

try:
    cookie_button = driver.find_element(By.CLASS_NAME, 'cookie-popup-with-overlay__button')
    cookie_button.click()
except NoSuchElementException:
    print("Cookie button not found.")

print('Waiting for the card-price 10 seconds...')
try:
    element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "flight-card-new"))
    )
    print("Flight found. Searching the price")
    price_carousel = driver.find_elements(By.CSS_SELECTOR, "carousel-container carousel-item")

    price_info = get_price_selected(price_carousel, date_object)
    print(price_info)
    driver.quit()
except TimeoutException:
    print("Flight not found. Try another date.")
    driver.quit()

