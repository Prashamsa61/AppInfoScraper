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
    name = "review_scraper"

    def __init__(self):
        chrome_options = Options()
        # chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=chrome_options)

        self.db_manager = DatabaseManager()
        self.db_manager.create_reviews_table()
        self.app_links = set()

    def start_requests(self):
        with open("../categories.csv", mode="r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                url = row["URL"]
                yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        self.driver.get(response.url)
        time.sleep(3)

        # Find all app links
        app_elements = self.driver.find_elements(By.XPATH, "//div[@jsname='qJTHM']//a")
        for app in app_elements:
            app_link = app.get_attribute("href")
            self.app_links.add(app_link)

        for app_url in self.app_links:
            yield scrapy.Request(
                url=app_url,
                callback=self.parse_app_review,
                meta={"app_url": app_url},
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

        # Check if extracted tile matches the title in app data
        app = next((app for app in app_data if app["title"] == title), None)
        if app:
            app_id = app["AppID"]
        else:
            self.logger.info("App not found")

        if app_id:
            self.logger.info(f"Title matched! App ID: {app_id}")

            # Click 'See All Reviews' button if available
            try:
                see_all_reviews_button = self.driver.find_element(
                    By.XPATH,
                    "//button[@jscontroller='soHxf']//span[contains(text(), 'See all reviews')]",
                )
                self.driver.execute_script(
                    "arguments[0].click();", see_all_reviews_button
                )
                time.sleep(3)
            except Exception:
                self.logger.info("No 'See All Reviews' button found.")

            # Scroll reviews section
            try:
                scroll = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//div[contains(@jsname,'rZHESd')]")
                    )
                )
                self.driver.execute_script("arguments[0].scrollIntoView();", scroll)
                time.sleep(2)
            except Exception:
                self.logger.info("Scrolling part not found")

            # Click dropdown for sorting reviews
            try:
                drop_down_arrow_main = self.driver.find_element(
                    By.XPATH,
                    "//div[contains(@id,'formFactor_2')]//i[text()='arrow_drop_down']",
                )
                self.driver.execute_script(
                    "arguments[0].click();", drop_down_arrow_main
                )
                time.sleep(3)
            except Exception:
                self.logger.info("No drop-down arrow found")

            main_tabs = ["Phone", "Chromebook", "Tablet", "Watch"]
            review_tabs = ["Most relevant", "Newest", "Most relevant"]
            reviews = []

            for main_tab in main_tabs:
                try:
                    main_tab_element = self.driver.find_element(
                        By.XPATH,
                        f"//div[contains(@class,'jO7h3c') and text()='{main_tab}']",
                    )
                    WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable(main_tab_element)
                    )
                    self.driver.execute_script(
                        "arguments[0].click();", main_tab_element
                    )
                    time.sleep(2)
                    self.logger.info(f"Clicked on '{main_tab}' tab.")
                except Exception:
                    self.logger.info(f"'{main_tab}' tab is not clickable, skipping.")

                # Click dropdown for sorting reviews
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

                        # Extract reviews
                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located(
                                (By.XPATH, "//div[@class='h3YV2d']")
                            )
                        )

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

            # Debugging: Check if reviews are extracted
            if not reviews:
                self.logger.info(f"No reviews found for {title}.")
            else:
                self.logger.info(f"Extracted {len(reviews)} reviews for {title}.")

            # Yield the final result outside loops
            yield {
                "app_id": app_id,
                "title": title,
                "app_url": app_url,
                "reviews": reviews,
            }
            self.db_manager.insert_review_data(app_id, reviews)

        else:
            self.logger.info(f"No matching title found in the database for: {title}")

    def closed(self, reason):
        self.driver.quit()
