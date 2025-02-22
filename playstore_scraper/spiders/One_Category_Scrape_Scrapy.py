###Scrapy for a category
import scrapy


class PlaystoreSpider(scrapy.Spider):
    name = "acategory"
    allowed_domains = ["play.google.com"]
    categories = [
        "ART_AND_DESIGN?hl=en",
    ]

    category_limits = 10
    start_urls = [
        f"https://play.google.com/store/apps/category/{category}"
        for category in categories
    ]

    category_counts = {
        category.split("?")[0]: 0 for category in categories
    }  # Track scraped items per category

    def parse(self, response):
        category = response.url.split("/")[-1].split("?")[0]  # Extract category name
        app_links = response.xpath("//div[contains(@class,'zuJxTd')]//a/@href").getall()

        for link in app_links:
            if self.category_counts[category] < self.category_limits:
                full_url = response.urljoin(link)
                self.category_counts[category] += 1
                yield response.follow(
                    full_url, self.parse_app, meta={"category": category}
                )

    def parse_app(self, response):
        category = response.meta.get("category")

        title = response.xpath("//h1/span/text()").get()
        version = response.xpath("//div[@class='reAt0'][1]/text()").get()
        rating = response.xpath("//div[@class='ClM7O']//div/text()").get()
        review_count = response.xpath(
            "//div[contains(@class,'g1rdde')][1]/text()"
        ).get()
        downloads = response.xpath(
            "//div[contains(@class,'wVqUob')][2]/div/text()"
        ).get()
        age_suitability = response.xpath(
            "//span[@itemprop='contentRating']//text()"
        ).get()
        updated_on = response.xpath("//div[contains(@class, 'xg1aie')]/text()").get()
        ads = response.xpath("//span[contains(@class, 'UIuSk')]/text()").get()

        yield {
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
