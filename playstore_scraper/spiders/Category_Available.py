import scrapy


class PlaystoreSpider(scrapy.Spider):
    name = "playstore"
    allowed_domains = ["play.google.com"]

    categories = [
        "ART_AND_DESIGN?hl=en",
        "AUTO_AND_VEHICLES?hl=en",
        "BOOKS_AND_REFERENCE?hl=en",
        "BUSINESS",
        "COMICS",
        "COMMUNICATION",
        "DATING",
        "EDUCATION",
        "ENTERTAINMENT",
        "EVENTS",
        "FINANCE",
        "FOOD_AND_DRINK?hl=en",
        "HEALTH_AND_FITNESS?hl=en",
        "HOUSE_AND_HOME?hl=en",
        "LIBRARIES_AND_DEMO?hl=en",
        "LIFESTYLE",
        "MAPS_AND_NAVIGATION?hl=en",
        "MUSIC_AND_AUDIO?hl=en",
        "NEWS_AND_MAGAZINES?hl=en",
        "PARENTING",
        "PERSONALIZATION",
        "PHOTOGRAPHY",
        "PRODUCTIVITY",
        "SHOPPING",
        "SOCIAL",
        "SPORTS",
        "TOOLS",
        "TRAVEL_AND_LOCAL?hl=en",
        "VIDEO_PLAYERS_AND_EDITORS?hl=en",
        "WEATHER",
        "ACTION",
        "ADVENTURE",
        "ARCADE",
        "BOARD",
        "CARD",
        "CASINO",
        "CASUAL",
        "EDUCATIONAL",
        "MUSIC",
        "PUZZLE",
        "RACING",
        "ROLE_PLAYING?h1=en",
        "SIMULATION",
        "SPORTS_GAMES?hl=en",
        "STRATEGY",
        "TRIVIA",
        "WORD",
    ]
    category_limits = 10

    start_urls = [
        f"https://play.google.com/store/apps/category/{category}"
        for category in categories
    ]

    category_counts = {
        category: 0 for category in categories
    }  # Track scraped items per category

    def parse(self, response):
        # Extract category name correctly, removing query parameters like ?hl=en
        category = response.url.split("/")[-1].split("?")[0]

        # Ensure category is initialized in category_counts to prevent KeyError
        if category not in self.category_counts:
            self.category_counts[category] = 0

        if self.category_counts[category] < self.category_limits:
            app_links = response.xpath(
                "//div[contains(@class,'VfPpkd')]//a/@href"
            ).getall()

            if not app_links:
                self.log(f"No app links found for {category}! Check XPath.")

            for link in app_links:
                full_link = response.urljoin(link)
                yield response.follow(
                    full_link, callback=self.parse_app, meta={"category": category}
                )

    def parse_app(self, response):
        category = response.meta.get("category")

        # Extract data
        title = response.xpath('//*[@id="yDmH0d"]//h1/span/text()').get()
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

        data = {
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

        self.save_to_csv(category, data)

    # def save_to_csv(self, category, data):
    #     """Saves the scraped data to a category-specific CSV file."""
    #     filename = f"{category}.csv"
    #     file_exists = os.path.isfile(filename)

    #     with open(filename, "a", newline="", encoding="utf-8") as file:
    #         writer = csv.DictWriter(file, fieldnames=data.keys())

    #         if not file_exists:
    #             writer.writeheader()

    #         writer.writerow(data)
