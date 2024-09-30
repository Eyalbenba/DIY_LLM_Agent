from WebCrawler import WebCrawler
import requests
from bs4 import BeautifulSoup
class LimitedWebCrawler(WebCrawler):
    def __init__(self, homepage, max_seen_urls_per_topic=500, blacklist=None, logger=None):
        """
        Initialize the limited web crawler system with a homepage, limits per topic, and optional blacklist.
        """
        super().__init__(
            homepage,
            max_seen_urls=max_seen_urls_per_topic * 6,  # Assuming 6 main topics
            blacklist=blacklist,
            logger=logger
        )

        # Topic-based tracking
        self.topic_counts = {
            "Circuits": 0,
            "Workshop": 0,
            "Craft": 0,
            "Cooking": 0,
            "Living": 0,
            "Teachers": 0
        }
        self.max_seen_urls_per_topic = max_seen_urls_per_topic

    def is_topic_limit_reached(self, topic):
        """
        Check if the limit for a specific topic has been reached.

        :param topic: The topic to check.
        :return: True if the limit for this topic has been reached, False otherwise.
        """
        return self.topic_counts.get(topic, 0) >= self.max_seen_urls_per_topic

    def update_topic_count(self, topic):
        """
        Increment the count for a specific topic.

        :param topic: The topic to increment the count for.
        """
        if topic in self.topic_counts:
            self.topic_counts[topic] += 1

    def crawl_and_process(self, content_extractor, log_frequency=100):
        """
        Crawl websites and process content, respecting the topic limits.

        :param content_extractor: An instance of ContentExtractor to process the content.
        :param log_frequency: How often (in terms of iterations) to log the topic count progress.
        """
        iteration_count = 0  # Initialize a counter to track iterations

        while self.to_visit and not all(
            self.is_topic_limit_reached(topic) for topic in self.topic_counts
        ):
            url = self.to_visit.pop(0)
            if url in self.visited_links or url in self.blacklist:
                continue

            self.logger.info(f"Visiting {url}...")
            self.visited_links.add(url)

            try:
                response = requests.get(url)
                response.raise_for_status()
                html_content = response.text
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Error fetching {url}: {e}")
                continue

            # Extract content from the HTML and determine the topic
            soup = BeautifulSoup(html_content, 'html.parser')
            topic = self.determine_topic(soup)

            if topic and not self.is_topic_limit_reached(topic):
                self.logger.info(f"Processing {topic} content from {url}...")
                content_extractor.extract_content_from_html(url, html_content)
                self.update_topic_count(topic)

                # Extract and add internal links to the list to visit next
                internal_links = self.extract_internal_links(url, html_content)
                self.to_visit.extend(internal_links)
            else:
                self.logger.info(f"Skipping {url}, topic limit reached or no valid topic identified.")
                # Extract and add internal links to the list to visit next
                internal_links = self.extract_internal_links(url, html_content)
                self.to_visit.extend(internal_links)

            # Increment the iteration count
            iteration_count += 1

            # Log progress every 'log_frequency' iterations
            if iteration_count % log_frequency == 0:
                self.log_progress()

    def log_progress(self):
        """
        Log the current progress of how many pages have been scraped for each topic.
        """
        self.logger.info("Current scraping progress:")
        self.logger.info(f"Links Visited: {len(self.visited_links)}")
        self.logger.info(f"Links Left to Visit: {len(self.to_visit)}")
        for topic, count in self.topic_counts.items():
            self.logger.info(f"Topic: {topic}, Pages scraped: {count}")

    def determine_topic(self, soup):
        """
        Determine the topic from the parsed HTML content.

        :param soup: BeautifulSoup object representing the parsed HTML content.
        :return: The identified topic as a string, or None if no valid topic is found.
        """
        topic_tag = soup.find("a", {"class": "category"})
        if topic_tag:
            category_text = topic_tag.text.strip()
            if category_text in self.topic_counts:
                return category_text
        self.logger.warning("No valid topic found for this page.")
        return None
