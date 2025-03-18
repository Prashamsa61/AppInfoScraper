import threading
import subprocess
import time


def run_spider(spider_name, delay=0):
    """Function to run a Scrapy spider with an optional delay."""
    if delay:
        time.sleep(delay)
    print(f"Starting {spider_name} spider...")
    subprocess.run(["scrapy", "crawl", spider_name])


# Create threads
scrapers_thread = threading.Thread(target=run_spider, args=("scrapers",))
reviews_thread = threading.Thread(target=run_spider, args=("reviews_scraper", 600))

# Start scrapers thread first
scrapers_thread.start()
reviews_thread.start()

# Wait for both spiders to complete
scrapers_thread.join()
reviews_thread.join()

print("Both spiders have finished execution.")
