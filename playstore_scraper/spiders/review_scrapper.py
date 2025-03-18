import logging
import scrapy
import csv
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from playstore_scraper.database import DatabaseManager


class ScrapySeleniumSpider(scrapy.Spider):
    name = "reviews_scraper"

    def __init__(self):
        chrome_options = Options()
        # chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=chrome_options)

        self.db_manager = DatabaseManager()
        self.db_manager.create_reviews_table()
        self.app_links = set()

    def start_requests(self):
        with open("categories.csv", mode="r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                url = row["URL"]
                yield scrapy.Request(url=url, callback=self.parse)

    def scroll_reviews_section(self, min_reviews=100, max_attempts=3):
        """Scroll until at least `min_reviews` are loaded or no more reviews appear."""
        try:
            scroll = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[contains(@jsname,'bN97Pc')]")
                )
            )

            previous_review_count = 0
            attempts = 0

            while attempts < max_attempts:
                current_reviews = self.driver.find_elements(
                    By.XPATH, "//div[@class='h3YV2d']"
                )
                review_count = len(current_reviews)
                self.logger.info(f"Current reviews loaded: {review_count}")

                if review_count >= min_reviews:
                    self.logger.info(
                        f"✅ Loaded {review_count} reviews. Stopping scroll."
                    )
                    break

                self.driver.execute_script(
                    "arguments[0].scrollTo(0, arguments[0].scrollHeight);", scroll
                )
                time.sleep(2)

                if review_count == previous_review_count:
                    attempts += 1
                    self.logger.info(
                        f"⚠️ No new reviews. Attempt {attempts}/{max_attempts}"
                    )
                else:
                    attempts = 0

                previous_review_count = review_count

            self.logger.info("🚀 Stopping scrolling process.")

        except Exception as e:
            self.logger.error(f"❌ Error while scrolling reviews: {str(e)}")

    def parse(self, response):
        self.driver.get(response.url)
        time.sleep(3)

        app_elements = self.driver.find_elements(By.XPATH, "//div[@jsname='qJTHM']//a")
        for app in app_elements:
            self.app_links.add(app.get_attribute("href"))

        for app_url in self.app_links:
            yield scrapy.Request(
                url=app_url, callback=self.parse_app_review, meta={"app_url": app_url}
            )

    def parse_app_review(self, response):
        app_url = response.meta["app_url"]
        self.driver.get(app_url)

        try:
            title = (
                WebDriverWait(self.driver, 10)
                .until(EC.presence_of_element_located((By.XPATH, "//h1/span")))
                .text.strip()
            )
        except Exception:
            self.logger.info("Error extracting app title")

        app_data = self.db_manager.read_database()

        # Initialize app id
        app_id = None

        # Check if extracted tile matches the title in app data
        app = next((app for app in app_data if app["title"] == title), None)
        if app:
            app_id = app["AppID"]
        else:
            self.logger.info("App not found")

        if app_id is None:
            self.logger.info(
                f"No matching title found in the database for: {title}. Skipping..."
            )
            return

        try:
            see_all_reviews_button = self.driver.find_element(
                By.XPATH,
                "//button[@jscontroller='soHxf']//span[contains(text(), 'See all reviews')]",
            )
            self.driver.execute_script("arguments[0].click();", see_all_reviews_button)
            time.sleep(3)
        except Exception:
            self.logger.info("No 'See All Reviews' button found.")

        self.scroll_reviews_section(min_reviews=100)

        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='h3YV2d']"))
        )

        reviews = []
        review_elements = self.driver.find_elements(By.XPATH, "//div[@class='h3YV2d']")
        reviewer_name_elements = self.driver.find_elements(
            By.XPATH, "//div[@class='X5PpBb']"
        )
        review_date_elements = self.driver.find_elements(
            By.XPATH, "//span[@class='bp9Aid']"
        )
        review_rating_elements = self.driver.find_elements(
            By.XPATH, "//div[@class='Jx4nYe']//div[@class='iXRFPc']"
        )

        for i in range(len(review_elements)):
            if len(reviews) >= 100:
                break

            review_text = (
                review_elements[i].text.strip() if i < len(review_elements) else None
            )
            reviewer_name = (
                reviewer_name_elements[i].text.strip()
                if i < len(reviewer_name_elements)
                else "Anonymous"
            )
            review_date = (
                review_date_elements[i].text.strip()
                if i < len(review_date_elements)
                else "Unknown"
            )
            review_rating = (
                review_rating_elements[i].get_attribute("aria-label").split()[1]
                if i < len(review_rating_elements)
                else "No Rating"
            )

            if review_text:
                reviews.append(
                    {
                        "review_text": review_text,
                        "reviewer_name": reviewer_name,
                        "review_date": review_date,
                        "review_rating": review_rating,
                    }
                )

        yield {
            "app_id": app_id,
            "title": title,
            "app_url": app_url,
            "reviews": reviews,
        }

        self.db_manager.insert_review_data(app_id, reviews)

    def closed(self, reason):
        self.driver.quit()
