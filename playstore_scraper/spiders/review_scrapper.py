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
    name = "review_Scraper"

    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=chrome_options)
        self.start_urls = self.load_urls_from_csv("../categories.csv")

        self.db_manager = DatabaseManager()
        self.db_manager.insert_review_data()

    def load_urls_from_csv(self, filename):
        urls = []
        self.category_mapping = {}

        try:
            with open(filename, mode="r", newline="", encoding="utf-8") as file:
                csv_reader = csv.DictReader(file)
                for row in csv_reader:
                    url = row["URL"].strip()
                    category = row["Category"].strip()
                    urls.append(url)
                    self.category_mapping[url] = category
        except Exception as e:
            self.logger.error(f"Error loading CSV file: {e}")

        return urls

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                self.parse_category_page,
                meta={"category": self.category_mapping[url]},
            )

    def parse_category_page(self, response):
        self.driver.get(response.url)
        category = response.meta["category"]
        app_links = []

        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[contains(@jscontroller,'jZ2Ncd')]//a")
                )
            )
            app_elements = self.driver.find_elements(
                By.XPATH, "//div[contains(@jsname,'K9a4Re')]//a"
            )
            for app_element in app_elements:
                app_link = app_element.get_attribute("href")
                if app_link and app_link not in app_links:
                    app_links.append(app_link)
        except Exception as e:
            self.logger.error(f"Error extracting app links from {response.url}: {e}")
            return

        for app_link in app_links:
            yield scrapy.Request(
                app_link, self.parse_app_page, meta={"category": category}
            )

    def parse_app_page(self, response):
        self.driver.get(response.url)
        category = response.meta["category"]

        try:
            title = self.driver.find_element(By.XPATH, "//h1/span").text.strip()
        except Exception:
            self.logger.info("Error extracting app title")
            return

        # Check if the app exists in DB
        if not self.db_manager.app_exists_in_playstore(title):
            self.logger.info(f"Skipping {title}, not found in database.")
            return

        app_id = self.db_manager.get_app_id(title)
        if app_id is None:
            self.logger.info(f"App '{title}' not found in database")
            return

        # Click 'See All Reviews' button if available
        try:
            see_all_reviews_button = self.driver.find_element(
                By.XPATH,
                "//button[@jscontroller='soHxf']//span[contains(text(), 'See all reviews')]",
            )
            if see_all_reviews_button:
                self.driver.execute_script(
                    "arguments[0].click();", see_all_reviews_button
                )
                time.sleep(3)
            else:
                review_button = self.driver.find_element(
                    By.XPATH,
                    "//div[contains(@class,'VMq4uf')]//button[@aria-label='See more information on Ratings and reviews']",
                )
                self.driver.execute_script("arguments[0].click();", review_button)
        except Exception:
            self.logger.info("No 'See All Reviews' button found.")

        try:
            # Scroll the reviews
            scroll = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[contains(@jsname,'rZHESd')]")
                )
            )
            if scroll:
                self.driver.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight);", scroll
                )
            time.sleep(2)
        except Exception:
            self.logger.info("Scrolling part not found")

        # Click dropdown for sorting reviews
        try:
            drop_down_arrow_main = self.driver.find_element(
                By.XPATH,
                "//div[contains(@id,'formFactor_2')]//i[text()='arrow_drop_down']",
            )
            self.driver.execute_script("arguments[0].click();", drop_down_arrow_main)
            time.sleep(3)
        except Exception:
            self.logger.info("No drop-down arrow found")

        main_tabs = ["Phone", "Chromebook", "Tablet", "Watch"]
        review_tabs = ["Most relevant", "Newest", "Most relevant"]
        reviews = []

        for main_tab in main_tabs:
            try:
                # Find the main tab element
                main_tab_element = self.driver.find_element(
                    By.XPATH,
                    f"//div[contains(@class,'jO7h3c') and text()='{main_tab}']",
                )

                # Try to wait for the main tab to be clickable
                WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable(main_tab_element)
                )

                # Click the main tab if it's clickable
                self.driver.execute_script("arguments[0].click();", main_tab_element)
                time.sleep(2)
                self.logger.info(f"Clicked on '{main_tab}' tab.")
            except Exception:
                # If the main tab is not clickable, log it and proceed to the review tab
                self.logger.info(
                    f"'{main_tab}' tab is not clickable, skipping to review tab."
                )

            # Click dropdown for sorting reviews of tab_name
            try:
                drop_down_arrow = self.driver.find_element(
                    By.XPATH, "//div[contains(@id,'sortBy_1')]//i"
                )
                self.driver.execute_script("arguments[0].click();", drop_down_arrow)
                time.sleep(3)
            except Exception:
                self.logger.info("No drop-down arrow found")

            for tab_name in review_tabs:
                try:
                    tab_element = self.driver.find_element(
                        By.XPATH,
                        f"//div[contains(@class,'jO7h3c') and text()='{tab_name}']",
                    )
                    self.driver.execute_script("arguments[0].click();", tab_element)
                    time.sleep(2)
                    self.logger.info(f"Clicked on '{tab_name}' tab.")

                    review_elements = self.driver.find_elements(
                        By.XPATH, "//div[@class='h3YV2d']"
                    )
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
                            review_elements[i].text.strip()
                            if i < len(review_elements)
                            else None
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
                            review_rating_elements[i]
                            .get_attribute("aria-label")
                            .split()[1]
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
                except Exception:
                    self.logger.info(f"No '{tab_name}' tab found.")

                yield {
                    "app_id": app_id,
                    "category": category,
                    "title": title,
                    "reviews": reviews,
                }
                self.db_manager.insert_review_data(app_id, reviews)

    def closed(self, reason):
        self.driver.quit()
