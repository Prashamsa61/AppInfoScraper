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
import os
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
from selenium.common.exceptions import StaleElementReferenceException


class PlaystoreSpider(scrapy.Spider):
    name = "scrapers"
    allowed_domains = ["play.google.com"]

    def __init__(self):
        # Read category data from CSV file
        self.categories = self.read_categories_from_csv("../categories.csv")
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
        """Read categories and their URLs from a CSV file with error handling."""
        categories = []

        # Check if file exists
        if not os.path.exists(file_path):
            print(f"Error: File '{file_path}' not found.")
            return categories

        try:
            with open(file_path, newline="", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)

                # Check if the CSV has the required columns
                if (
                    reader.fieldnames is None
                    or "Category" not in reader.fieldnames
                    or "URL" not in reader.fieldnames
                ):
                    print("Error: CSV file is missing 'Category' or 'URL' columns.")
                    return categories
                for row in reader:
                    # Ensure row data is valid
                    if not row.get("Category") or not row.get("URL"):
                        print(f"Warning: Skipping row with missing data: {row}")
                        continue

                    categories.append(
                        {"category": row["Category"].strip(), "url": row["URL"].strip()}
                    )

            # Check if any categories were read
            if not categories:
                print("Warning: CSV file is empty or contains only invalid rows.")

        except Exception as e:
            print(f"Error reading CSV file: {e}")

        return categories

    def parse_category_page(self, response):
        category = response.meta["category"]
        print(f"Attempting to load URL: {response.url}")

        self.driver.get(response.url)

        category_buttons = {
            "Top Free": "ct|apps_topselling_free",
            "Top Grossing": "ct|apps_topgrossing",
            "Top Paid": "ct|apps_topselling_paid",
        }

        for ranking_category, button_id in category_buttons.items():
            try:
                attempts = 3
                for _ in range(attempts):
                    try:
                        button = self.driver.find_element(By.ID, button_id)
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                            button,
                        )
                        self.driver.execute_script("arguments[0].click();", button)
                        time.sleep(6)
                        break
                    except StaleElementReferenceException:
                        print("Element became stale, retrying...")
                        time.sleep(2)
            except Exception as e:
                self.logger.error(f"Could not click {ranking_category}: {e}")
                continue  # Move to the next category if this one fails

            # Extract and store all app links first
            app_links = []
            app_elements = self.driver.find_elements(
                By.XPATH,
                "//section[contains(@jscontroller,'IgeFAf')]//div[contains(@jscontroller,'tKHFxf')]/a",
            )

            for app_element in app_elements:
                app_link = app_element.get_attribute("href")
                app_links.append(app_link)

            # Now process each app link
            for app_link in app_links:
                yield scrapy.Request(
                    url=app_link,
                    callback=self.parse_app_page,
                    meta={
                        "category": category,
                        "ranking_category": ranking_category,
                        "category_url": response.url,
                    },
                    dont_filter=True,
                )

        # Process additional apps if ranking category apps were not found
        additional_app_links = []
        additional_apps = self.driver.find_elements(
            By.XPATH,
            "//div[contains(@jscontroller,'jZ2Ncd')]//div[contains(@class,'ULeU3b neq64b')]//a",
        )

        for app_element in additional_apps:
            app_link = app_element.get_attribute("href")
            additional_app_links.append(app_link)

        for app_link in additional_app_links:
            yield scrapy.Request(
                url=app_link,
                callback=self.parse_app_page,
                meta={
                    "category": category,
                    "ranking_category": "No Rank",
                    "category_url": response.url,
                },
                dont_filter=True,
            )

    def parse_app_page(self, response):
        category = response.meta["category"]
        ranking_category = response.meta["ranking_category"]

        print(f"Attempting to load URL: {response.url}")

        self.driver.get(response.url)
        time.sleep(15)  # Allow page to load

        # Wait for the main content area
        wait = WebDriverWait(self.driver, 10)
        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[contains(@jscontroller,'lpwuxb')]")
            )
        )

        wait.until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    " //div[@class='xg1aie']",
                )
            )
        )

        # Click the arrow button if available
        try:
            buttons = self.driver.find_elements(
                By.XPATH, "//div[contains(@jscontroller,'lpwuxb')]//button"
            )
            button_2 = self.driver.find_elements(
                By.XPATH,
                '//button[@aria-label="See more information on About this app"]',
            )

            if buttons:
                self.driver.execute_script("arguments[0].click();", buttons[0])
                time.sleep(3)
            else:
                self.driver.execute_script("arguments[0].click();", button_2[0])
                time.sleep(3)

        except Exception as e:
            logging.warning(f"Arrow button click skipped or failed: {e}")

        wait.until(
            EC.presence_of_all_elements_located(
                (By.XPATH, "//div[contains(@class,'G1zzid')]")
            )
        )
        wait.until(
            EC.presence_of_all_elements_located(
                (
                    By.XPATH,
                    "//div[contains(text(), 'Version')]/following-sibling::div",
                )
            )
        )

        wait.until(
            EC.presence_of_all_elements_located(
                (
                    By.XPATH,
                    "//div[@class='sMUprd'][div[contains(text(), 'Updated on')]]/div[@class='reAt0']",
                )
            )
        )

        # Extract app price
        price = self.extract_price()

        # Extract data individually for each key
        title_elements = self.driver.find_elements(
            By.XPATH, "//h1/span[contains(@itemprop,'name')]"
        )
        rating_elements = self.driver.find_elements(
            By.XPATH,
            "//div[contains(@class,'TT9eCd') and contains(@aria-label, 'Rated')] | //div[contains(@class,'jILTFe')]",
        )

        version_elements = self.driver.find_element(
            By.XPATH, "//div[contains(text(), 'Version')]/following-sibling::div"
        )

        review_count_elements = self.driver.find_elements(
            By.XPATH, "//div[contains(@class,'g1rdde') and contains(text(), 'reviews')]"
        )
        downloads_elements = self.driver.find_elements(
            By.XPATH,
            "//div[contains(@class,'wVqUob')][div[2][text()='Downloads']]/div[1]",
        )
        requires_android_elements = self.driver.find_element(
            By.XPATH, "//div[.='Requires Android']/following-sibling::div"
        )

        age_suitability_elements = self.driver.find_elements(
            By.XPATH, "//span[@itemprop='contentRating']"
        )

        updated_on_elements = self.driver.find_element(
            By.XPATH,
            "//div[@class='sMUprd'][div[contains(text(), 'Updated on')]]/div[@class='reAt0']",
        )

        ads_elements = self.driver.find_elements(
            By.XPATH, "//span[contains(@class, 'UIuSk')]"
        )
        in_app_purchases_elements = self.driver.find_elements(
            By.XPATH,
            "//div[@class='sMUprd'][div[1][contains(text(), 'In-app purchases')]]/div[2]",
        )

        # Collect raw data for all fields
        raw_data = {
            "title": title_elements[0].text if title_elements else "No title",
            "rating": rating_elements[0].text if rating_elements else "Rating Missing",
            "version": version_elements[0].text if version_elements else "No Version",
            "review_count": review_count_elements[0].text
            if review_count_elements
            else "No review",
            "downloads": downloads_elements[0].text
            if downloads_elements
            else "No downloads",
            "Requires_android": requires_android_elements[0].text
            if requires_android_elements
            else "Not given",
            "age_suitability": age_suitability_elements[0].text
            if age_suitability_elements
            else "No age-suitability",
            "updated_on": updated_on_elements.text
            if updated_on_elements
            else "Not given",
            "ads": ads_elements[0].text if ads_elements else "No ad",
            "In_app_purchases": in_app_purchases_elements[0].text
            if in_app_purchases_elements
            else "Free",
            "category": category,
            # "url": response.url,
            "ranking_category": ranking_category,
            "price": price,
        }

        yield raw_data
        self.db_manager.insert_app_data()

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
                    By.XPATH, "//div[contains(@class,'u4ICaf')]//button"
                )
                price_text = price_element.get_attribute("aria-label").strip()

                # Remove "Buy" if it's at the start or end
                price_text = re.sub(r"^(Buy\s*|\s*Buy)$", "", price_text).strip()

                return price_text
            except Exception:
                return "Not Available"

        return "Not Available"

    def closed(self, reason):
        """Close the Selenium WebDriver and database connection when the spider finishes."""
        self.logger.info(f"Spider closed due to: {reason}")

        if hasattr(self, "driver") and self.driver:
            if len(self.driver.window_handles) > 1:
                self.driver.close()
            else:
                self.driver.quit()

        if hasattr(self.db_manager, "close"):
            self.db_manager.close()
