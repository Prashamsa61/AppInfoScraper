import scrapy
import re
from playstore_scraper.database import DatabaseManager


class PlayStoreSpider(scrapy.Spider):
    name = "google_play"
    start_urls = ["https://play.google.com/store/apps/details?id=com.kiloo.subwaysurf"]
    visited_urls = set()

    def __init__(self):
        self.db_manager = DatabaseManager()
        self.db_manager.create_app_links_table()

    def parse(self, response):
        # Extract app ID from the URL
        app_id_match = re.search(r"id=([a-zA-Z0-9_\.]+)", response.url)
        app_id = app_id_match.group(1) if app_id_match else "UNKNOWN"

        # Extract app logo
        logo = response.xpath("//div[contains(@class,'RhBWnf')]/img/@src").get(
            default="missing"
        )

        # Extract "Offered By"
        offered_by = response.xpath(
            "//div[contains(@class,'Vbfug auoIOc')]//span/text()"
        ).get()
        if not offered_by:
            offered_by = "Unknown"

        # Extract Ranking Category
        ranking_text = response.xpath(
            "//div[contains(@class,'Uc6QCc')]//span[contains(text(), 'top')]/text()"
        ).get()
        if ranking_text:
            ranking_cleaned = re.search(r"(top\s+\w+)", ranking_text, re.IGNORECASE)
            ranking_category = (
                ranking_cleaned.group(1).title() if ranking_cleaned else "No rank"
            )
        else:
            ranking_category = "No rank"

        # Extract Categories from hrefs
        category_hrefs = response.xpath(
            "//a[contains(@jsname,'hSRGPd') and contains(@href, '/store/apps/category/')]/@href"
        ).extract()
        categories = [
            re.search(r"/category/([A-Z_]+)", href).group(1)
            for href in category_hrefs
            if re.search(r"/category/([A-Z_]+)", href)
        ]
        category_name = ", ".join(categories) if categories else "UNKNOWN"

        # Extarct the description
        description = response.xpath("//div[contains(@class,'bARER')]//text()").getall()
        description = " ".join(description).strip()

        # Prepare and store the app data
        data = {
            "app_id": app_id,
            "offered_by": offered_by,
            "ranking_category": ranking_category,
            "category_name": category_name,
            "description": description,
            "app_url": response.url,
            "logo": logo,
        }
        self.db_manager.insert_app_link_data(data)

        yield data

        # Extract and follow links to other apps
        app_links = response.xpath(
            "//a[contains(@class,'Si6A0c nT2RTe')]/@href"
        ).extract()
        for link in app_links:
            full_link = response.urljoin(link)
            if full_link not in self.visited_urls:
                self.visited_urls.add(full_link)
                yield response.follow(full_link, callback=self.parse)
