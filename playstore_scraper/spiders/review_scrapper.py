import scrapy
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from playstore_scraper.database import DatabaseManager


class PlayStore(scrapy.Spider):
    name = "fullScrape"
    allowed_domains = ["play.google.com"]
    category = ["ART_AND_DESIGN?hl=en"]
    category_limit = 15
    start_urls = [
        f"https://play.google.com/store/apps/category/{cat}" for cat in category
    ]
    category_counts = {cat.split("?")[0]: 0 for cat in category}

    def __init__(self):
        """Initialize Selenium WebDriver and Database."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        self.db_manager = DatabaseManager()
        self.db_manager.create_reviews_table()

        self.driver = webdriver.Chrome(options=chrome_options)

    def parse(self, response):
        """Extract app links from category page."""
        category = response.url.split("/")[-1].split("?")[0]
        app_links = response.xpath("//div[contains(@class,'zuJxTd')]//a/@href").getall()

        for link in app_links:
            if self.category_counts[category] < self.category_limit:
                full_url = response.urljoin(link)
                self.category_counts[category] += 1
                yield scrapy.Request(
                    url=full_url, callback=self.parse_app, meta={"category": category}
                )

    def parse_app(self, response):
        """Extract app details and reviews, using auto-incrementing app ID."""
        category = response.meta.get("category")
        self.driver.get(response.url)
        time.sleep(2)

        # Extract app title
        try:
            title = self.driver.find_element(By.XPATH, "//h1/span").text.strip()
        except Exception as e:
            self.logger.info(f"Error extracting app title ")
            return

        if not self.db_manager.app_exists_in_playstore(title):
            self.logger.info(
                f"Skipping review extraction for {title}, not found in playstore_data.db apps table."
            )
            return

        app_id = self.db_manager.get_app_id(title)
        if app_id is None:
            self.logger(f"App'{title}' not found in database")
            return

        # Click the "See All Reviews" button if available
        try:
            see_all_reviews_button = self.driver.find_element(
                By.XPATH,
                "//button[@jscontroller='soHxf']//span[contains(text(), 'See all reviews')]",
            )
            self.driver.execute_script("arguments[0].click();", see_all_reviews_button)
            time.sleep(3)
        except:
            self.logger.info(f"No 'See All Reviews' button found .")

        # Extract reviews
        reviews = []
        review_elements = self.driver.find_elements(By.XPATH, "//div[@class='h3YV2d']")
        reviewer_name_elements = self.driver.find_elements(
            By.XPATH, "//div[@class='X5PpBb']"
        )
        review_date_elements = self.driver.find_elements(
            By.XPATH, "//span[@class='bp9Aid']"
        )
        review_rating_elements = self.driver.find_elements(
            By.XPATH, "//div[@class='iXRFPc']//span[@aria-hidden='true']"
        )

        # Ensure review data is extracted properly
        for i in range(len(review_elements)):
            review_text = (
                review_elements[i].text.strip()
                if i < len(review_elements) and review_elements[i].text.strip()
                else None
            )
            reviewer_name = (
                reviewer_name_elements[i].text.strip()
                if i < len(reviewer_name_elements)
                else None
            )
            review_date = (
                review_date_elements[i].text.strip()
                if i < len(review_date_elements)
                else None
            )
            review_rating = (
                review_rating_elements[i].text.strip()
                if i < len(review_rating_elements)
                else None
            )

            # Only include non-empty reviews
            if review_text:
                reviews.append(
                    {
                        "review_text": review_text,
                        "reviewer_name": reviewer_name or "Anonymous",
                        "review_date": review_date or "Unknown",
                        "review_rating": review_rating or "No Rating",
                    }
                )

        # Insert reviews data into the database
        if reviews:
            self.db_manager.insert_review_data(app_id, reviews)

        yield {
            "app_id": app_id,
            "category": category,
            "title": title,
            "reviews": reviews,
        }

    def closed(self, reason):
        """Close Selenium WebDriver."""
        self.driver.quit()
