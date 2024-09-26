import pickle
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import random
class WebCrawler:
    def __init__(self, homepage, max_seen_urls=10, blacklist=None, logger=None):
        """
        Initialize the web crawler system with a homepage, crawling limits, and optional blacklist.

        :param homepage: URL to start crawling from.
        :param max_seen_urls: Maximum number of pages to visit in a single iteration.
        :param blacklist: Set of blacklisted URLs to exclude from the crawl.
        :param logger: Logger instance to log the crawl process.
        """
        self.homepage = homepage
        self.max_seen_urls = max_seen_urls
        self.blacklist = set(blacklist) if blacklist else set()
        self.to_visit = [homepage]
        self.visited_links = set(self.blacklist)
        self.logger = logger   # Use provided logger or default


    def extract_internal_links(self, base_url, html_content):
      """
      Extract all internal links from a webpage using BeautifulSoup.

      :param base_url: URL of the webpage to crawl for links.
      :param html_content: The fetched HTML content of the webpage.
      :return: A list of internal links.
      """
      soup = BeautifulSoup(html_content, 'html.parser')
      internal_links = []

      # Get all group sections to handle multiple sitemap sections like Circuits, Workshop, etc.
      group_sections = soup.find_all('div', class_='group-section')

      # Loop through each group section and extract the links
      for section in group_sections:
          sitemap_list = section.find('ul', class_='sitemap-listing')
          if sitemap_list:
              for link in sitemap_list.find_all('a', href=True):
                  href = link['href']
                  full_url = urljoin(base_url, href)
                  if full_url not in self.visited_links:
                      internal_links.append(full_url)

      # Fallback to extract general links if no sitemap sections are found
      if not group_sections:
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(base_url, href)

            # Check if 'www.instructables.com' is in the full URL and it has not been visited yet
            if 'www.instructables.com' in full_url and full_url not in self.visited_links:
                internal_links.append(full_url)

      return internal_links

    def crawl_and_process(self, content_extractor, random_jump_frequency=50):
        """
        Crawl websites to collect internal links and process content immediately.

        :param content_extractor: An instance of ContentExtractor to process the content immediately.
        :param random_jump_frequency: How often to perform a random jump (default is every 5 iterations).
        """
        iteration_count = 0

        while self.to_visit and len(self.visited_links) < self.max_seen_urls:
            iteration_count += 1

            # Randomly jump to a different URL in the to_visit list based on frequency
            if iteration_count % random_jump_frequency == 0 and len(self.to_visit) > 1:
                # Pick a random index from the list
                random_index = random.randint(0, len(self.to_visit) - 1)
                url = self.to_visit.pop(random_index)
                self.logger.info(f"Random jump to {url}")
            else:
                # Default behavior: pop the first URL
                url = self.to_visit.pop(0)

            if url in self.visited_links or url in self.blacklist:
                continue

            self.logger.info(f"Visiting {url}...")
            self.visited_links.add(url)

            # Fetch the page content
            try:
                response = requests.get(url)
                response.raise_for_status()
                html_content = response.text
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Error fetching {url}: {e}")
                continue

            # Check if "sitemap" is in the URL and skip content extraction
            if "sitemap" in url.lower():
                self.logger.info(f"Skipping content extraction for sitemap URL: {url}")
            else:
                # Process the content immediately with the content extractor
                content_extractor.extract_content_from_html(url, html_content)

            # Extract internal links and update the to_visit list
            internal_links = self.extract_internal_links(url, html_content)
            self.to_visit.extend(internal_links)
            self.logger.info(f"Total Links to extract: {len(self.to_visit)}")

        return self.visited_links

