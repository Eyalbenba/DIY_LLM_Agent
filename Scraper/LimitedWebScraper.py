from datetime import datetime
import os
from Scraper.LimitedWebCrawler import LimitedWebCrawler
from Scraper.ContentExtractorV2 import ContentExtractor
from ScrapeLogger import ScraperLogger
from pymongo import MongoClient  # Add MongoClient for MongoDB
from MongoDB.MongoClient import MongoDBClient  # Import MongoDBClient class

class LimitedWebScraper:
    def __init__(self, homepage,mongo_uri, max_seen_urls_per_topic=500, blacklist=None, save_content=True, main_save_path=None, log_to_console=True):
        """
        Initialize the main web scraper with the homepage, limits, and configurations.
        """
        current_time = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
        log_file_name = f'scrape_log_{current_time}.txt'

        if main_save_path:
            log_dir = os.path.join(main_save_path, "scrape_logs")
            log_path = os.path.join(log_dir, log_file_name)
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
        else:
            log_path = log_file_name
            log_dir = 'logs'

        # Logger initialization
        self.logger = ScraperLogger(log_file=log_path, log_dir=log_dir, log_to_console=log_to_console).get_logger()

        # MongoDB client initialization
        if mongo_uri:
            self.mongo_client = MongoDBClient(mongo_uri,
                                              logger=self.logger)  # Pass logger for logging MongoDB operations
        else:
            self.mongo_client = None  # If no MongoDB URI is provided, disable MongoDB usage

        # Crawler and content extractor initialization
        self.crawler = LimitedWebCrawler(
            homepage,
            max_seen_urls_per_topic=max_seen_urls_per_topic,
            blacklist=blacklist,
            logger=self.logger,
        )
        self.extractor = ContentExtractor(
            mongo_client=self.mongo_client,  # Pass the MongoDB client to the extractor
            save_content=save_content,
            main_save_path=main_save_path,
            logger=self.logger,
            use_embeddings=True
        )

    def run(self):
        """
        Run the web scraper: Crawl the website and process content immediately.
        """
        self.logger.info("Starting crawling and processing content...")

        while self.crawler.to_visit and not all(
            self.crawler.is_topic_limit_reached(topic) for topic in self.crawler.topic_counts
        ):
            # Crawl and process the page
            self.crawler.crawl_and_process(self.extractor)

        self.logger.info("Crawling finished. All topic limits reached or no more pages to visit.")

        if self.mongo_client:
            self.mongo_client.close()


