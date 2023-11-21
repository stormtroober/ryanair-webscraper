from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By

def print_element_details(elements):
    """
    Prints details of a Selenium WebElement or a list of WebElements in a readable format.

    :param elements: A Selenium WebElement or a list of WebElements.
    """
    if isinstance(elements, WebElement):
        elements = [elements]  # Convert single WebElement into a list

    for idx, element in enumerate(elements):
        tag_name = element.tag_name
        class_name = element.get_attribute('class')
        text = element.text
        # Truncate the text for brevity
        truncated_text = text[:30] + '...' if len(text) > 30 else text
        print(f"Element {idx}: Tag={tag_name}, Class={class_name}, Text={truncated_text}")

def extract_price_info(text, flightDate):
    """
    Extracts currency, amount, and flight date from a text string and returns them in a dictionary.

    Args:
    text (str): Text string containing currency and amount.
    flightDate (str): String representing the flight date.

    Returns:
    dict: Dictionary with keys 'currency', 'amount', and 'date'.
    """
    try:
        # Split the text to separate currency and amount
        parts = text.split()
        
        # Extracting currency
        currency = parts[0]

        # Combine amount parts if separated by a comma and convert to float
        amount_str = ''.join(parts[1:]).replace(',', '.')

        # Converting amount string to a float
        amount = float(amount_str)

        # Returning the result in a dictionary including the flight date
        return {
            'currency': currency,
            'amount': amount,
            'date': flightDate.strftime("%Y-%m-%d")
        }
    except Exception as e:
        print(f"Error extracting price info: {e}")
        return None


def get_price_selected(priceCarousel, flightDate):
    priceSelected = None
    for box in priceCarousel:
        child_elements = box.find_elements(By.XPATH, "./*")
        for element in child_elements:
            isSelected = 'date-item--selected' in element.get_attribute('class').split()
            if isSelected:
                priceSelected = box.find_element(By.CSS_SELECTOR, 'ry-price')
                break
    return extract_price_info(priceSelected.text, flightDate)