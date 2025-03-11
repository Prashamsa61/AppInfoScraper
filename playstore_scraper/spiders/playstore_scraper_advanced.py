"""
Google Play Store Scraper

This Scrapy spider uses Selenium to scrape app details from the Google Play Store.
It extracts data such as:
- App title
- Rating
- Version
- Number of reviews
- Downloads
- Required Android version
- Age suitability
- Last update date
- Presence of ads
- In-app purchases
- Price
- Ranking category
- Category

How it works:
1. Reads category names and URLs from a CSV file.
2. Visits each category page and navigates through different ranking sections
   (Top Free, Top Grossing, Top Paid).
3. Clicks on app links to visit individual app pages and extract details.
4. Saves extracted data into an SQLite database using the DatabaseManager.

"""

import scrapy
import csv
import time
import re
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from playstore_scraper.database import DatabaseManager


class PlaystoreSpider(scrapy.Spider):
    name = "scrapers"

    def __init__(self):
        # Read category data from CSV file
        self.categories = self.read_categories_from_csv("../output/categories.csv")
        self.category_counters = {}
        # Set up Selenium WebDriver
        chrome_options = Options()
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        self.driver = webdriver.Chrome(options=chrome_options)

        # Initialize database manager and create table if not exists
        self.db_manager = DatabaseManager()
        self.db_manager.create_apps_table()

    def start_requests(self):
        # Start scraping each category URL
        for item in self.categories:
            self.category_counters[item["category"]] = 0
            yield scrapy.Request(
                url=item["url"],
                callback=self.parse_category_page,
                meta={"category": item["category"]},
            )

    def read_categories_from_csv(self, file_path):
        """Read categories and their URLs from CSV file."""
        categories = []
        with open(file_path, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                categories.append({"category": row["Category"], "url": row["URL"]})
        return categories

    def parse_category_page(self, response):
        """Parse the category page and extract app URLs from different ranking categories."""

        category = response.meta["category"]
        self.driver.get(response.url)

        # Define category button IDs for rankings
        category_buttons = {
            "Top Free": "ct|apps_topselling_free",
            "Top Grossing": "ct|apps_topgrossing",
            "Top Paid": "ct|apps_topselling_paid",
        }

        for ranking_category, button_id in category_buttons.items():
            try:
                # Click category button to load apps
                button = self.driver.find_element(By.ID, button_id)
                self.driver.execute_script("arguments[0].click();", button)
                time.sleep(3)

                # Extract app URLs
                app_elements = self.driver.find_elements(
                    By.XPATH,
                    "//section[contains(@jscontroller,'IgeFAf')]//div[contains(@class,'ULeU3b neq64b')]//a",
                )

                # Extract data for first 2 apps
                for i, app_element in enumerate(app_elements[:2]):
                    app_link = app_element.get_attribute("href")
                    yield scrapy.Request(
                        url=app_link,
                        callback=self.parse_app_page,
                        meta={
                            "category": category,
                            "ranking_category": ranking_category,
                            "category_url": response.url,
                        },
                    )

            except Exception as e:
                self.logger.error(f"Could not click {ranking_category}: {e}")

    def parse_app_page(self, response):
        category = response.meta["category"]
        ranking_category = response.meta["ranking_category"]
        category_url = response.meta["category_url"]

        self.driver.get(response.url)
        time.sleep(2)

        # Click the arrow button before extracting details
        try:
            wait = WebDriverWait(self.driver, 5)
            buttons = wait.until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, "//div[@class='VMq4uf']//button")
                )
            )
            if buttons:
                buttons[0].click()
                time.sleep(1)
        except Exception as e:
            logging.warning(f"Arrow button click skipped or failed: {e}")

        # Extract app price
        price = self.extract_price()

        # XPaths for extracting various app details
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

        extracted_data = {
            key: self.driver.find_elements(By.XPATH, xpath)
            for key, xpath in xpaths.items()
        }

        raw_data = {
            key: extracted_data[key][0].text if extracted_data[key] else None
            for key in xpaths
        }
        raw_data.update(
            {
                "category": category,
                "ranking_category": ranking_category,
                "price": price,
            }
        )

        cleaned_data = self.preprocess_data(raw_data)

        try:
            # Insert app data into database
            self.db_manager.insert_app_data(cleaned_data)
            yield cleaned_data
        finally:
            # Return to category page
            self.driver.get(category_url)
            time.sleep(3)

    def preprocess_data(self, data):
        def clean_numeric_value(value):
            if not value or not isinstance(value, str):
                return "Not Available"
            try:
                value = value.replace("+", "").strip()
                if "K" in value:
                    return int(float(value.replace("K", "")) * 1000)
                elif "M" in value:
                    return int(float(value.replace("M", "")) * 1000000)
                return int(value)
            except ValueError:
                return "Not Available"

        return {
            "category": data["category"],
            "title": data["title"],
            "rating": data["rating"].replace("\nstar", "") if data["rating"] else None,
            "version": data["version"] if data["version"] else "Not Available",
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
            "requires_android": data["Requires_android"]
            if data["Requires_android"]
            else "Not Available",
            "In_app_purchases": data["In_app_purchases"]
            if data["In_app_purchases"]
            else "No in-app-purchases",
            "price": data["price"] if data["price"] else "Free",
            "ranking_category": data["ranking_category"],
        }

    def extract_price(self):
        """Extract price of the app."""

        try:
            install_button = self.driver.find_element(
                By.XPATH, "//button[contains(@aria-label, 'Install')]"
            )
            if install_button:
                return "Free"
        except Exception:
            try:
                price_element = self.driver.find_element(
                    By.XPATH, "(//div[contains(@class,'u4ICaf')]//button)[1]"
                )
                price_text = price_element.get_attribute("aria-label")
                if "$" in price_text:
                    return re.sub(r"\s*Buy\s*", "", price_text).strip()
            except Exception:
                return "Not Available"
        return "Not Available"

    def closed(self, reason):
        """Close the Selenium WebDriver and database connection when the spider finishes."""
        self.driver.quit()
        if hasattr(self.db_manager, "close"):
            self.db_manager.close()

