# Import necessary libraries
import scrapy
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time


class PlayStoreSpider(scrapy.Spider):
    """
    A Scrapy spider that uses Selenium to scrape app rankings and prices
    from the Google Play Store.

    This spider:
    - Navigates to a specified category page on the Play Store.
    - Clicks on category tabs (Top Free, Top Grossing, Top Paid).
    - Extracts app details such as title, link, and price.
    - Clicks on each app to retrieve its price (if applicable).
    - Returns the extracted data as a Scrapy item.
    """

    name = "ranking"
    allowed_domains = ["play.google.com"]
    start_urls = [
        "https://play.google.com/store/apps/category/BOOKS_AND_REFERENCE?hl=en"
    ]

    def __init__(self):
        # Set up Selenium WebDriver with Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        self.driver = webdriver.Chrome(options=chrome_options)

    def parse(self, response):
        # Open the Play Store category page in Selenium
        self.driver.get(response.url)
        time.sleep(3)  # Wait for the page to load

        # Dictionary mapping category names to their button IDs
        categories = {
            "Top Free": "ct|apps_topselling_free",
            "Top Grossing": "ct|apps_topgrossing",
            "Top Paid": "ct|apps_topselling_paid",
        }

        for category_name, button_id in categories.items():
            try:
                # Click the button to open the category
                button = self.driver.find_element(By.ID, button_id)
                self.driver.execute_script("arguments[0].click();", button)
                time.sleep(3)  # Wait for apps to load

                # Locate all app elements in the category
                app_elements = self.driver.find_elements(
                    By.XPATH,
                    "//section[contains(@jscontroller,'IgeFAf')]//div[contains(@class,'ULeU3b neq64b')]",
                )

                # Extract details of the first 5 apps in the category
                for i in range(5):
                    if i >= len(
                        app_elements
                    ):  # Handle cases where there are fewer than 5 apps
                        self.logger.warning(
                            f"Not enough apps in {category_name}. Skipping app {i + 1}."
                        )
                        break

                    try:
                        app = app_elements[i]  # Select the app element by index

                        # Get the app title
                        title_element = app.find_element(
                            By.XPATH, ".//div[contains(@class,'ubGTjb')][1]"
                        )
                        app_title = title_element.text

                        # Get the app link
                        app_link_element = app.find_element(By.TAG_NAME, "a")
                        app_link = app_link_element.get_attribute("href")

                        # Click the app link to open the app details page
                        self.driver.execute_script(
                            "arguments[0].click();", app_link_element
                        )
                        time.sleep(3)  # Wait for the app page to load

                        # Initialize price variable
                        price = " "

                        try:
                            # Check if the app has an "Install" button (indicating a free app)
                            install_button = self.driver.find_element(
                                By.XPATH, "//button[contains(@aria-label, 'Install')]"
                            )
                            if install_button:
                                price = "Free"

                        except Exception:
                            # If no "Install" button is found, check for a price button (e.g., "$11.05 Buy")
                            try:
                                price_element = self.driver.find_element(
                                    By.XPATH,
                                    "(//div[contains(@class,'u4ICaf')]//button)[1]",
                                )
                                price_text = price_element.get_attribute("aria-label")

                                # Extract the price if it contains a "$" symbol
                                if "$" in price_text:
                                    price = re.sub(r"\s*Buy\s*", "", price_text).strip()
                                else:
                                    price = "Not Available"
                            except Exception:
                                price = "Not Available"

                        # Navigate back to the category page
                        self.driver.back()
                        time.sleep(3)  # Wait for the page to reload

                        # Yield extracted data as a Scrapy item
                        yield {
                            "category": category_name,
                            "title": app_title,
                            "link": app_link,
                            "price": price,
                        }

                    except Exception as e:
                        self.logger.error(
                            f"Could not process app {i + 1} under {category_name}: {e}"
                        )

            except Exception as e:
                self.logger.error(f"Could not click {category_name}: {e}")

    def closed(self, reason):
        """Close the browser when the spider finishes."""
        self.driver.quit()
