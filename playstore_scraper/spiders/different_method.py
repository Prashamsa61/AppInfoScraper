# #Scrape the code going to main page and back need to integrate to one_category and all done
# import scrapy
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.common.exceptions import NoSuchElementException
# import time

# class PlaystoreSpider(scrapy.Spider):
#     name = "category"
#     allowed_domains = ["play.google.com"]
#     start_urls = [
#         "https://play.google.com/store/apps/category/ART_AND_DESIGN?hl=en"
#     ]

#     def __init__(self):
#         """Initialize Selenium WebDriver"""
#         chrome_options = webdriver.ChromeOptions()
#         # chrome_options.add_argument("--headless")  # Run headless
#         chrome_options.add_argument("--disable-gpu")
#         chrome_options.add_argument("--no-sandbox")
#         self.driver = webdriver.Chrome(options=chrome_options)

#     def parse(self, response):
#         """Load category page, iterate over buttons, extract app details, and return back"""
#         start_url = response.url
#         self.driver.get(start_url)
#         time.sleep(3)  # Allow page to load

#         # Find category buttons to click
#         category_buttons = self.driver.find_elements(By.XPATH, "//div[contains(@class,'b6SkTb')]")

#         for idx, button in enumerate(category_buttons):
#             self.logger.info(f"Clicking category button {idx + 1}/{len(category_buttons)}")

#             # Click on category button
#             self.driver.execute_script("arguments[0].click();", button)
#             time.sleep(2)

#             # Extract app links & price **before entering the app pages**
#             app_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class,'YMlj6b')]//div/a[@class='Si6A0c itIJzb']")
#             app_links = [app.get_attribute("href") for app in app_elements]

#             prices = []
#             for app in app_elements:
#                 try:
#                     price_element = app.find_element(By.XPATH, "//div[contains(@class,'cXFu1')]//span[@class='sT93pb w2kbF ePXqnb']")
#                     price = price_element.text
#                 except NoSuchElementException:
#                     price = "Free"
#                 prices.append(price)

#             self.logger.info(f"Found {len(app_links)} apps in this category")

#             # Iterate over app links
#             for i, link in enumerate(app_links):
#                 self.logger.info(f"Processing app {i + 1}/{len(app_links)}: {link}")

#                 # Navigate to the app page
#                 self.driver.get(link)
#                 time.sleep(2)

#                 # Click "Read More" button if present
#                 try:
#                     button = self.driver.find_element(By.XPATH, "//div[@class='VMq4uf']//button")
#                     if button.is_displayed():
#                         self.driver.execute_script("arguments[0].click();", button)
#                         time.sleep(2)
#                 except NoSuchElementException:
#                     self.logger.info("No expandable 'Read More' section found for this app.")

#                 # Extract app details
#                 try:
#                     title = self.driver.find_element(By.XPATH, "//h1/span").text
#                 except NoSuchElementException:
#                     title = "N/A"

#                 try:
#                     rating = self.driver.find_element(By.XPATH, "//div[@class='ClM7O']//div").text
#                 except NoSuchElementException:
#                     rating = "N/A"

#                 app_data = {
#                     "category": "ART_AND_DESIGN",
#                     "title": title,
#                     "rating": rating.replace("star", ""),
#                     "price": prices[i] if i < len(prices) else "Unknown",
#                 }

#                 yield app_data

#                 # Navigate back to category page
#                 self.driver.get(start_url)
#                 time.sleep(2)

#             # Move to the next category button
#             self.driver.get(start_url)
#             time.sleep(2)

#     def closed(self, reason):
#         """Close the Selenium WebDriver when the spider finishes."""
#         self.driver.quit()


import scrapy
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import time


class PlaystoreSpider(scrapy.Spider):
    name = "category"
    allowed_domains = ["play.google.com"]

    start_urls = [
        "https://play.google.com/store/apps/category/ART_AND_DESIGN?hl=en",
        "https://play.google.com/store/apps/category/GAME_ACTION?hl=en",
        "https://play.google.com/store/apps/category/BOOKS_AND_REFERENCE?hl=en",
    ]

    def __init__(self):
        """Initialize Selenium WebDriver"""
        chrome_options = webdriver.ChromeOptions()
        # chrome_options.add_argument("--headless")  # Uncomment for headless mode
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        self.driver = webdriver.Chrome(options=chrome_options)

    def parse(self, response):
        """Load each category page and extract apps"""
        category_url = response.url
        category_name = category_url.split("/")[-1].split("?")[
            0
        ]  # Extract category name from URL
        self.driver.get(category_url)
        time.sleep(3)  # Allow page to load

        # Find category buttons
        category_buttons = self.driver.find_elements(
            By.XPATH, "//div[contains(@class,'b6SkTb')]"
        )

        for idx, button in enumerate(category_buttons):
            self.logger.info(
                f"Clicking category button {idx + 1}/{len(category_buttons)} for {category_name}"
            )
            self.driver.execute_script("arguments[0].click();", button)
            time.sleep(2)

            self.extract_apps(category_name)

    def extract_apps(self, category_name):
        """Extract app details from the category page"""
        app_elements = self.driver.find_elements(
            By.XPATH, "//div[contains(@class,'YMlj6b')]//div/a[@class='Si6A0c itIJzb']"
        )
        app_links = [app.get_attribute("href") for app in app_elements]

        prices = []
        for app in app_elements:
            try:
                price_element = app.find_element(
                    By.XPATH,
                    ".//div[contains(@class,'cXFu1')]//span[@class='sT93pb w2kbF ePXqnb']",
                )
                price = price_element.text
            except NoSuchElementException:
                price = "Free"
            prices.append(price)

        self.logger.info(f"Found {len(app_links)} apps in {category_name}")

        # Iterate over app links
        for i, link in enumerate(app_links):
            self.logger.info(f"Processing app {i + 1}/{len(app_links)}: {link}")
            self.driver.get(link)
            time.sleep(2)

            # Click "Read More" button if present
            try:
                button = self.driver.find_element(
                    By.XPATH, "//div[@class='VMq4uf']//button"
                )
                if button.is_displayed():
                    self.driver.execute_script("arguments[0].click();", button)
                    time.sleep(2)
            except NoSuchElementException:
                self.logger.info("No expandable 'Read More' section found.")

            # Extract app details
            try:
                title = self.driver.find_element(By.XPATH, "//h1/span").text
            except NoSuchElementException:
                title = "N/A"

            try:
                rating = self.driver.find_element(
                    By.XPATH, "//div[@class='ClM7O']//div"
                ).text
            except NoSuchElementException:
                rating = "N/A"

            app_data = {
                "category": category_name,
                "title": title,
                "rating": rating.replace("star", ""),
                "price": prices[i] if i < len(prices) else "Unknown",
            }

            yield app_data

    def closed(self, reason):
        """Close the Selenium WebDriver when the spider finishes."""
        self.driver.quit()
