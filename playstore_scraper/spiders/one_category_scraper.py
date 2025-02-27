import scrapy
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from playstore_scraper.database import DatabaseManager


class PlaystoreSpider(scrapy.Spider):
    name = "acategory"
    allowed_domains = ["play.google.com"]
    categories = [
        "ART_AND_DESIGN?hl=en",
        "BUSINESS",
        "COMICS",
    ]

    category_limits = 15
    start_urls = [
        f"https://play.google.com/store/apps/category/{category}"
        for category in categories
    ]

    category_counts = {category.split("?")[0]: 0 for category in categories}

    def __init__(self):
        """Initialize Selenium WebDriver and DatabaseManager."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        self.driver = webdriver.Chrome(options=chrome_options)
        self.db_manager = DatabaseManager()

        self.db_manager.create_apps_table()

    def parse(self, response):
        """Extract app links from category page."""
        category = response.url.split("/")[-1].split("?")[0]
        app_links = response.xpath("//div[contains(@class,'zuJxTd')]//a/@href").getall()

        for link in app_links:
            if self.category_counts[category] < self.category_limits:
                full_url = response.urljoin(link)
                self.category_counts[category] += 1
                yield scrapy.Request(
                    url=full_url, callback=self.parse_app, meta={"category": category}
                )

    def parse_app(self, response):
        """Use Selenium to click the button and extract data."""
        category = response.meta.get("category")
        self.driver.get(response.url)
        time.sleep(2)

        try:
            # Click the button to reveal hidden details
            button = self.driver.find_element(
                By.XPATH, "//div[@class='VMq4uf']//button"
            )
            self.driver.execute_script("arguments[0].click();", button)
            time.sleep(2)
        except:
            self.logger.info("Button not found or already clicked.")

        try:
            title = self.driver.find_element(By.XPATH, "//h1/span").text
            rating = self.driver.find_element(
                By.XPATH, "//div[@class='ClM7O']//div"
            ).text
            version = self.driver.find_element(
                By.XPATH, "//div[@class='reAt0'][1]"
            ).text
            review_count = self.driver.find_element(
                By.XPATH, "//div[contains(@class,'g1rdde')][1]"
            ).text
            downloads = self.driver.find_element(
                By.XPATH, "//div[contains(@class,'wVqUob')][2]/div"
            ).text
            age_suitability = self.driver.find_element(
                By.XPATH, "//span[@itemprop='contentRating']"
            ).text
            updated_on = self.driver.find_element(
                By.XPATH, "//div[contains(@class, 'xg1aie')]"
            ).text
            ads = self.driver.find_element(
                By.XPATH, "//span[contains(@class, 'UIuSk')]"
            ).text
        except:
            self.logger.info("Error extracting some fields.")
            return

        app_data = {
            "category": category,
            "title": title,
            "rating": rating,
            "version": version,
            "review_count": review_count,
            "downloads": downloads,
            "age_suitability": age_suitability,
            "updated_on": updated_on,
            "ads": ads,
        }

        self.db_manager.insert_app_data(app_data)

        yield app_data

    def closed(self, reason):
        """Close Selenium WebDriver and DatabaseManager."""
        self.driver.quit()
        self.db_manager.close()
