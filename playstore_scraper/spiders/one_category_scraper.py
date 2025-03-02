import scrapy
import time
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from playstore_scraper.database import DatabaseManager
from datetime import datetime
from selenium.common.exceptions import NoSuchElementException


class PlaystoreSpider(scrapy.Spider):
    name = "acategory"
    allowed_domains = ["play.google.com"]
    categories = {}

    def __init__(self):
        """Initialize Selenium WebDriver and DatabaseManager."""
        chrome_options = Options()
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        self.driver = webdriver.Chrome(options=chrome_options)
        self.db_manager = DatabaseManager()
        self.db_manager.create_apps_table()

        # Load categories from the CSV file
        csv_file_path = r"../output/categories.csv"
        self.categories = self.load_categories_from_csv(csv_file_path)
        self.category_limits = 2
        self.category_counts = {category: 0 for category in self.categories}

    def start_requests(self):
        """Generate requests for each category."""
        for category, url in self.categories.items():
            yield scrapy.Request(
                url=url, callback=self.parse, meta={"category": category}
            )

    def parse(self, response):
        """Extract app links from category page."""
        category = response.meta["category"]
        app_links = response.xpath("//div[contains(@class,'zuJxTd')]//a/@href").getall()

        for link in app_links[: self.category_limits]:
            if self.category_counts[category] < self.category_limits:
                full_url = response.urljoin(link)
                self.category_counts[category] += 1
                yield scrapy.Request(
                    url=full_url, callback=self.parse_app, meta={"category": category}
                )

    def parse_app(self, response):
        """Use Selenium to extract app details."""
        category = response.meta["category"]
        self.driver.get(response.url)
        time.sleep(2)

        try:
            button = self.driver.find_element(
                By.XPATH, "//div[@class='VMq4uf']//button"
            )
            if button.is_displayed():
                self.driver.execute_script("arguments[0].click();", button)
                time.sleep(2)
        except NoSuchElementException:
            self.logger.info("No expandable 'Read More' section found for this app.")

        try:
            title = self.driver.find_element(By.XPATH, "//h1/span").text
        except NoSuchElementException:
            self.logger.warning("Title not found.")
            title = None

        try:
            rating = self.driver.find_element(
                By.XPATH, "//div[@class='ClM7O']//div"
            ).text
        except NoSuchElementException:
            self.logger.warning("Rating not found.")
            rating = None

        try:
            version = self.driver.find_element(
                By.XPATH,
                "(//div[@class='reAt0'])[1] | //div[contains(@class, 'q078ud') and contains(text(), 'Version')]/following-sibling::div[@class='reAt0']",
            ).text
        except NoSuchElementException:
            self.logger.warning("Version not found.")
            version = None

        try:
            review_count = self.driver.find_element(
                By.XPATH, "//div[contains(@class,'g1rdde')][1]"
            ).text
        except NoSuchElementException:
            self.logger.warning("Review count not found.")
            review_count = None

        try:
            downloads = self.driver.find_element(
                By.XPATH, "//div[contains(@class,'wVqUob')][2]/div"
            ).text
        except NoSuchElementException:
            self.logger.warning("Downloads count not found.")
            downloads = None

        try:
            age_suitability = self.driver.find_element(
                By.XPATH, "//span[@itemprop='contentRating']"
            ).text
        except NoSuchElementException:
            self.logger.warning("Age suitability not found.")
            age_suitability = None

        try:
            updated_on = self.driver.find_element(
                By.XPATH, "//div[contains(@class, 'xg1aie')]"
            ).text
        except NoSuchElementException:
            self.logger.warning("Updated date not found.")
            updated_on = None

        try:
            ads = self.driver.find_element(
                By.XPATH, "//span[contains(@class, 'UIuSk')]"
            ).text
        except NoSuchElementException:
            self.logger.warning("Ads information not found.")
            ads = None
        updated_on = datetime.strptime(updated_on, "%b %d, %Y").strftime("%Y/%m/%d")

        app_data = {
            "category": category,
            "title": title,
            "rating": rating.replace("star", ""),
            "version": version,
            "review_count": review_count.replace("reviews", "").strip(),
            "downloads": downloads,
            "age_suitability": age_suitability.replace("Rated for", "").strip(),
            "updated_on": updated_on,
            "ads": ads,
        }

        self.db_manager.insert_app_data(app_data)
        yield app_data

    def load_categories_from_csv(self, csv_file_path):
        categories = {}
        try:
            with open(csv_file_path, mode="r", encoding="utf-8") as file:
                reader = csv.reader(file)
                next(reader)
                for row in reader:
                    category = row[0]
                    url = row[1]
                    categories[category] = url
        except FileNotFoundError:
            self.logger.error(f"CSV file not found at: {csv_file_path}")
        except Exception as e:
            self.logger.error(f"Error reading CSV file: {str(e)}")

        if not categories:
            self.logger.warning("No categories found in the CSV file.")
        return categories

    def closed(self, reason):
        """Close Selenium WebDriver and DatabaseManager."""
        self.driver.quit()
        self.db_manager.close()
