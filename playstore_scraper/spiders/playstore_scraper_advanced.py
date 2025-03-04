import scrapy
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
import time
import re

from playstore_scraper.database import DatabaseManager


class PlaystoreSpider(scrapy.Spider):
    name = "scraper"
    category_limit = 5

    def __init__(self):
        # Read URLs from CSV file
        self.categories = self.read_categories_from_csv("../output/categories.csv")
        self.category_counters = {}

        # Set up Selenium WebDriver
        chrome_options = Options()
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        self.driver = webdriver.Chrome(options=chrome_options)

        # Import DataBase file
        self.db_manager = DatabaseManager()
        self.db_manager.create_apps_table()

    def start_requests(self):
        """Iterate over categories and yield requests with category metadata"""
        for item in self.categories:
            self.category_counters[item["category"]] = 0  # Initialize counter
            yield scrapy.Request(
                url=item["url"],
                callback=self.parse_category_page,
                meta={"category": item["category"]},
            )

    def click_arrow_button(self):
        """Clicks the arrow button to extract all app info if available"""
        try:
            wait = WebDriverWait(self.driver, 5)
            buttons = wait.until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, "//div[@class='VMq4uf']//button")
                )
            )

            if buttons:
                buttons[0].click()
                print("Clicked the first button successfully.")
            else:
                print("No buttons found.")
        except Exception:
            print("No 'Arrow' button found or already clicked")

    def read_categories_from_csv(self, file_path):
        """Read the categories.csv file and get category names and URLs"""
        categories = []
        with open(file_path, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                categories.append({"category": row["Category"], "url": row["URL"]})
        return categories

    def click_category_button(self, button_id):
        """Clicks the category tab (Top Free, Top Grossing, Top Paid)"""
        try:
            wait = WebDriverWait(self.driver, 15)
            button = wait.until(EC.element_to_be_clickable((By.ID, button_id)))
            button.click()
            time.sleep(3)
            return True
        except Exception as e:
            print(f"Button {button_id} not found or already selected. Error: {e}")
            return False

    def parse_category_page(self, response):
        """Extracts the app links from the category page and visits them."""
        category = response.meta["category"]
        self.driver.get(response.url)

        ranking_categories = {
            "Top Free": "ct|apps_topselling_free",
            "Top Grossing": "ct|apps_topgrossing",
            "Top Paid": "ct|apps_topselling_paid",
        }

        all_apps = {}

        for rank_name, rank_id in ranking_categories.items():
            if self.click_category_button(rank_id):
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//div[contains(@class,'ULeU3b neq64b')]//a")
                    )
                )  # Wait for app elements to load

            # Find all app links and price
            app_links = self.driver.find_elements(
                By.XPATH, "//div[contains(@class,'ULeU3b neq64b')]//a"
            )
            # app_prices = self.driver.find_elements(
            #     By.XPATH, "//span [contains(@class,'sT93pb w2kbF ePXqnb')]/text()"
            # )
            app_prices = [
                price.text
                for price in self.driver.find_elements(
                    By.XPATH, "//span[contains(@class,'sT93pb w2kbF ePXqnb')]"
                )
            ]

            # app_titles = self.driver.find_elements(
            #     By.XPATH, "//div[contains(@class,'ubGTjb')][1]"
            # )
            app_titles = [
                title.text
                for title in self.driver.find_elements(
                    By.XPATH, "//div[contains(@class,'ubGTjb')][1]"
                )
            ]

            # Extract href and price
            app_data = []
            for i, link in enumerate(app_links):
                app_urls = link.get_attribute("href")
                print(f"Extracted URL: {app_urls}")  # Debugging step

                if not app_urls:  # Check if it's empty or None
                    print("WARNING: Extracted app URL is empty or None!")

                app_title = app_titles[i] if i < len(app_titles) else "Unknown"
                app_price = app_prices[i] if i < len(app_prices) else "Free"

                app_data.append(
                    {"url": app_urls, "price": app_price, "title": app_title}
                )

                if app_urls in all_apps:
                    print(f"Appending ranking category to {app_urls}")
                    all_apps[app_urls]["ranking_category"].append(rank_name)
                    print(f"Updated entry: {all_apps[app_urls]}")

                else:
                    all_apps[app_urls] = {
                        "url": app_urls,
                        "title": app_title,
                        "price": app_price,
                        "ranking_category": [rank_name],
                    }

            # Ensure exactly 5 apps are processed
            for app in app_data[: self.category_limit]:
                yield scrapy.Request(
                    url=app["url"],
                    callback=self.parse_app_page,
                    meta={
                        "category": category,
                        "category_url": response.url,
                        "price": app["price"],
                        "ranking_category": app.get("ranking_category", ["Unknown"]),
                    },
                )

    def parse_app_page(self, response):
        """Extracts app details from the app page."""
        category = response.meta["category"]
        category_url = response.meta["category_url"]
        price = response.meta["price"]
        ranking_category = response.meta["ranking_category"]

        self.driver.get(response.url)
        time.sleep(2)

        # Click Arrow button to load more app_info
        self.click_arrow_button()

        # Define XPaths
        xpaths = {
            "title": "//h1/span",
            "rating": "//div[@class='ClM7O']//div",
            "version": "//div[contains(@class, 'q078ud') and contains(text(), 'Version')]/following-sibling::div[@class='reAt0']",
            "review_count": "//div[contains(@class,'g1rdde')][1]",
            "downloads": "//div[contains(@class,'wVqUob')][2]/div",
            "Requires_android": "//div[contains(@class, 'q078ud') and contains(text(), 'Requires Android')]/following-sibling::div[@class='reAt0']",
            "age_suitability": "//span[@itemprop='contentRating']",
            "updated_on": "//div[contains(@class, 'q078ud') and contains(text(), 'Updated on')]/following-sibling::div[@class='reAt0']",
            "ads": "//span[contains(@class, 'UIuSk')]",
            "In_app_purchases": "//div[@class='sMUprd'][div[1][contains(text(), 'In-app purchases')]]/div[2]",
        }

        # Extract elements
        extracted_data = {
            key: self.driver.find_elements(By.XPATH, xpath)
            for key, xpath in xpaths.items()
        }

        # Extract text values
        raw_data = {
            key: extracted_data[key][0].text if extracted_data[key] else None
            for key in xpaths
        }
        raw_data.update(
            {
                "category": category,
                # "app_url": response.url,
                "price": price,
                "ranking_category": ranking_category,
            }
        )

        # Pre-process extracted data
        cleaned_data = self.preprocess_data(raw_data)

        try:
            self.db_manager.insert_app_data(cleaned_data)
            yield cleaned_data

        finally:
            self.driver.get(category_url)
            time.sleep(3)

    def preprocess_data(self, data):
        """Cleans extracted data"""

        def clean_numeric_value(value):
            """Convert K/M+ notation to integer values"""
            if "K" in value:
                return int(float(value.replace("K", "")) * 1000)
            elif "M" in value:
                return int(float(value.replace("M", "").replace("+", "")) * 1000000)
            return value

        return {
            "category": data["category"],
            # "app_url": data["app_url"],
            "title": data["title"],
            "rating": data["rating"].replace("\nstar", "") if data["rating"] else None,
            "version": data["version"],
            "review_count": clean_numeric_value(
                re.sub(r"[^\dKM]", "", data["review_count"])
            )
            if data["review_count"]
            else None,
            "downloads": clean_numeric_value(data["downloads"]),
            "age_suitability": re.sub(r"[^0-9+]", "", data["age_suitability"])
            if data["age_suitability"]
            else None,
            "updated_on": data["updated_on"] if data["updated_on"] else "Not Available",
            "ads": data["ads"] if data["ads"] else "No Ad",
            "requires_android": data["Requires_android"],
            "In_app_purchases": data["In_app_purchases"]
            if data["In_app_purchases"]
            else "None",
            "price": data["price"] if data["price"] else "Free",
            "ranking_category": ", ".join(data["ranking_category"]),
        }

    def closed(self, reason):
        self.driver.quit()
        self.db_manager.close()
