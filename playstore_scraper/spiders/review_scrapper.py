import scrapy
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from playstore_scraper.database import DatabaseManager


class ScrapySeleniumSpider(scrapy.Spider):
    name = "reviews_scraper"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set up Selenium WebDriver
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        self.driver = webdriver.Chrome(options=chrome_options)

        # Initialize database manager
        self.db_manager = DatabaseManager()
        self.db_manager.create_reviews_table()

    def start_requests(self):
        """Generates Scrapy requests for each app ID in the database."""
        base_url = "https://play.google.com/store/apps/details?id="
        app_ids = self.db_manager.read_database()

        for app_id in app_ids:
            url = base_url + app_id
            yield scrapy.Request(
                url=url, callback=self.parse_app_review, meta={"app_id": app_id}
            )

    def scroll_reviews_section(self, max_attempts=5, max_reviews=2000):
        """Scroll until either `max_reviews` are loaded or no more reviews appear."""
        try:
            scroll_area = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[contains(@jsname,'bN97Pc')]")
                )
            )

            previous_review_count = 0
            attempts = 0

            while attempts < max_attempts:
                review_elements = self.driver.find_elements(
                    By.XPATH, "//div[@class='h3YV2d']"
                )
                review_count = len(review_elements)
                self.logger.info(f"Loaded {review_count} reviews so far...")

                if review_count >= max_reviews:
                    self.logger.info(
                        f"✅ Reached max reviews limit ({max_reviews}). Stopping scroll."
                    )
                    break

                # Scroll to the bottom of the reviews section
                self.driver.execute_script(
                    "arguments[0].scrollTo(0, arguments[0].scrollHeight);", scroll_area
                )
                time.sleep(2)

                if review_count == previous_review_count:
                    attempts += 1  # No new reviews, count attempts
                    self.logger.info(
                        f"⚠️ No new reviews. Attempt {attempts}/{max_attempts}"
                    )
                else:
                    attempts = 0

                previous_review_count = review_count

        except Exception as e:
            self.logger.error(f"❌ Error while scrolling reviews: {str(e)}")

    def parse_app_review(self, response):
        """Parses reviews for the given app page and stores them."""
        app_id = response.meta["app_id"]

        # Open URL in Selenium WebDriver
        self.driver.get(response.url)

        # Wait until the url is loaded
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='tU8Y5c']"))
        )

        # Click "See all reviews" button if available
        try:
            see_all_reviews_button = self.driver.find_element(
                By.XPATH,
                "//button[@jscontroller='soHxf']//span[contains(text(), 'See all reviews')]",
            )
            self.driver.execute_script("arguments[0].click();", see_all_reviews_button)
            time.sleep(3)
        except Exception:
            self.logger.info("No 'See All Reviews' button found.")

        self.scroll_reviews_section()

        # Wait for reviews to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='h3YV2d']"))
        )

        # Extract reviews
        reviews = []
        review_elements = self.driver.find_elements(By.XPATH, "//div[@class='h3YV2d']")

        # Limit to 2000 reviews
        max_reviews = 2000
        review_elements = review_elements[:max_reviews]

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

        # Yield extracted data
        yield {
            "app_id": app_id,
            "reviews": reviews,
        }

        # Save to database
        self.db_manager.insert_review_data(app_id, reviews)

    def closed(self, reason):
        """Cleanup Selenium WebDriver when spider is closed."""
        self.driver.quit()
