from datetime import datetime
import os
from Scraper.LimitedWebCrawler import LimitedWebCrawler
from Scraper.ContentExtractor import ContentExtractor
from Scraper.ScrapeLogger import ScraperLogger
class LimitedWebScraper:
    def __init__(self, homepage, max_seen_urls_per_topic=500, blacklist=None, save_content=True, main_save_path=None, log_to_console=True):
        """
        Initialize the main web scraper with the homepage, limits, and configurations.
        """
        current_time = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
        log_file_name = f'scrape_log_{current_time}.txt'

        if main_save_path:
            log_path = os.path.join(main_save_path, log_file_name)
            log_dir = main_save_path
        else:
            log_path = log_file_name
            log_dir = 'logs'

        # Logger initialization
        self.logger = ScraperLogger(log_file=log_path, log_dir=log_dir, log_to_console=log_to_console).get_logger()

        # Crawler and content extractor initialization
        self.crawler = LimitedWebCrawler(
            homepage,
            max_seen_urls_per_topic=max_seen_urls_per_topic,
            blacklist=blacklist,
            logger=self.logger
        )
        self.extractor = ContentExtractor(save_content, main_save_path=main_save_path, logger=self.logger)

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



if __name__ == "__main__":
    homepage = "https://www.instructables.com/sitemap"

    # List of blacklisted URLs to exclude
    blacklist = [
        "https://www.instructables.com/",
        "https://www.instructables.com/projects/",
        "https://www.instructables.com/contest/",
        "https://www.instructables.com/teachers/",
        "https://www.instructables.com/contact/",
        "https://www.instagram.com/instructables/",
        "https://www.tiktok.com/@instructables",
        "https://www.autodesk.com/company/legal-notices-trademarks/terms-of-service-autodesk360-web-services/instructables-terms-of-service-june-5-2013",
        "https://www.instructables.com/circuits/",
        "https://www.instructables.com/workshop/",
        "https://www.instructables.com/craft/",
        "https://www.instructables.com/cooking/",
        "https://www.instructables.com/living/",
        "https://www.instructables.com/outside/",
        "https://www.instructables.com/teachers/",
        "https://www.instructables.com/about/",
        "https://www.instructables.com/create/",
        "https://www.instructables.com/sitemap/",
        "https://www.instructables.com/how-to-write-a-great-instructable/",
        'https://www.autodesk.com/company/legal-notices-trademarks/privacy-statement',
        'https://www.autodesk.com/company/legal-notices-trademarks',
        'https://www.autodesk.com'
    ]
    # main_save_path = "/content/drive/MyDrive/Instructables_Scraped_Data"
    # Initialize the main scraper class
    scraper = LimitedWebScraper(homepage=homepage, blacklist=blacklist, save_content=False)

    # Run the full scraping process
    scraper.run()