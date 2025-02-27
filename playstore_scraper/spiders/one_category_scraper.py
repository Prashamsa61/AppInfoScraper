import scrapy
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from playstore_scraper.database import DatabaseManager


class PlaystoreSpider(scrapy.Spider):
    name = "acategory"
    allowed_domains = ["play.google.com"]
    categories = {
        "ART_AND_DESIGN": "https://play.google.com/store/apps/category/ART_AND_DESIGN?hl=en",
        "AUTO_AND_VEHICLES": "https://play.google.com/store/apps/category/AUTO_AND_VEHICLES?hl=en",
        "BOOKS_AND_REFERENCE": "https://play.google.com/store/apps/category/BOOKS_AND_REFERENCE?hl=en",
        "BUSINESS": "https://play.google.com/store/apps/category/BUSINESS",
        "COMICS": "https://play.google.com/store/apps/category/COMICS",
        "COMMUNICATION": "https://play.google.com/store/apps/category/COMMUNICATION",
        "DATING": "https://play.google.com/store/apps/category/DATING",
        "EDUCATION": "https://play.google.com/store/apps/category/EDUCATION",
        "ENTERTAINMENT": "https://play.google.com/store/apps/category/ENTERTAINMENT",
        "EVENTS": "https://play.google.com/store/apps/category/EVENTS",
        "FINANCE": "https://play.google.com/store/apps/category/FINANCE",
        "FOOD_AND_DRINK": "https://play.google.com/store/apps/category/FOOD_AND_DRINK?hl=en",
        "HEALTH_AND_FITNESS": "https://play.google.com/store/apps/category/HEALTH_AND_FITNESS?hl=en",
        "HOUSE_AND_HOME": "https://play.google.com/store/apps/category/HOUSE_AND_HOME?hl=en",
        "LIBRARIES_AND_DEMO": "https://play.google.com/store/apps/category/LIBRARIES_AND_DEMO?hl=en",
        "LIFESTYLE": "https://play.google.com/store/apps/category/LIFESTYLE",
        "MAPS_AND_NAVIGATION": "https://play.google.com/store/apps/category/MAPS_AND_NAVIGATION?hl=en",
        "MUSIC_AND_AUDIO": "https://play.google.com/store/apps/category/MUSIC_AND_AUDIO?hl=en",
        "NEWS_AND_MAGAZINES": "https://play.google.com/store/apps/category/NEWS_AND_MAGAZINES?hl=en",
        "PARENTING": "https://play.google.com/store/apps/category/PARENTING",
        "PERSONALIZATION": "https://play.google.com/store/apps/category/PERSONALIZATION",
        "PHOTOGRAPHY": "https://play.google.com/store/apps/category/PHOTOGRAPHY",
        "PRODUCTIVITY": "https://play.google.com/store/apps/category/PRODUCTIVITY",
        "SHOPPING": "https://play.google.com/store/apps/category/SHOPPING",
        "SOCIAL": "https://play.google.com/store/apps/category/SOCIAL",
        "SPORTS": "https://play.google.com/store/apps/category/SPORTS",
        "TOOLS": "https://play.google.com/store/apps/category/TOOLS",
        "TRAVEL_AND_LOCAL": "https://play.google.com/store/apps/category/TRAVEL_AND_LOCAL?hl=en",
        "VIDEO_PLAYERS_AND_EDITORS": "https://play.google.com/store/apps/category/VIDEO_PLAYERS_AND_EDITORS?hl=en",
        "WEATHER": "https://play.google.com/store/apps/category/WEATHER",
        "ACTION": "https://play.google.com/store/apps/category/ACTION",
        "ADVENTURE": "https://play.google.com/store/apps/category/ADVENTURE",
        "ARCADE": "https://play.google.com/store/apps/category/ARCADE",
        "BOARD": "https://play.google.com/store/apps/category/BOARD",
        "CARD": "https://play.google.com/store/apps/category/CARD",
        "CASINO": "https://play.google.com/store/apps/category/CASINO",
        "CASUAL": "https://play.google.com/store/apps/category/CASUAL",
        "EDUCATIONAL": "https://play.google.com/store/apps/category/EDUCATIONAL",
        "MUSIC": "https://play.google.com/store/apps/category/MUSIC",
        "PUZZLE": "https://play.google.com/store/apps/category/PUZZLE",
        "RACING": "https://play.google.com/store/apps/category/RACING",
        "ROLE_PLAYING": "https://play.google.com/store/apps/category/ROLE_PLAYING?hl=en",
        "SIMULATION": "https://play.google.com/store/apps/category/SIMULATION",
        "SPORTS_GAMES": "https://play.google.com/store/apps/category/SPORTS_GAMES?hl=en",
        "STRATEGY": "https://play.google.com/store/apps/category/STRATEGY",
        "TRIVIA": "https://play.google.com/store/apps/category/TRIVIA",
        "WORD": "https://play.google.com/store/apps/category/WORD",
    }

    start_urls = list(categories.values())
    category_limits = 1
    category_counts = {category: 0 for category in categories}

    def __init__(self):
        """Initialize Selenium WebDriver and DatabaseManager."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        self.driver = webdriver.Chrome(options=chrome_options)
        self.db_manager = DatabaseManager()
        self.db_manager.create_apps_table()

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


