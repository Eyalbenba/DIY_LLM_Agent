from Scraper.WebCrawler import WebCrawler
from Scraper.ContentExtractor import ContentExtractor
from Scraper.ScrapeLogger import ScraperLogger
import pickle
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os
import json
import hashlib
import trafilatura
from langchain_community.embeddings import HuggingFaceBgeEmbeddings

import os
from datetime import datetime

class WebScraper:
    def __init__(self, homepage, max_seen_urls=10, blacklist=None, save_content=True, main_save_path=None):
        """
        Initialize the main web scraper with the homepage, limits, and configurations.
        """
        # Generate a unique log file name based on the current date and time
        current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file_name = f'scrape_log_{current_time}.txt'

        if main_save_path:
            log_path = os.path.join(main_save_path, log_file_name)
            log_dir = main_save_path
        else:
            log_path = log_file_name
            log_dir = 'logs'

        # Initialize the logger with the generated log file name
        self.logger = ScraperLogger(log_file=log_path, log_dir=log_dir).get_logger()
        self.crawler = WebCrawler(homepage, max_seen_urls, blacklist, logger=self.logger)
        self.extractor = ContentExtractor(save_content, main_save_path=main_save_path, logger=self.logger)


    def run(self):
        """
        Run the web scraper: Crawl the website and process content immediately.
        """
        self.logger.info("Starting crawling and processing content...")
        self.crawler.crawl_and_process(self.extractor)


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
    scraper = WebScraper(homepage=homepage, max_seen_urls=100000, blacklist=blacklist, save_content=False)

    # Run the full scraping process
    scraper.run()