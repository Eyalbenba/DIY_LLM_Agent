import requests
from bs4 import BeautifulSoup
import os
import json
import hashlib
import trafilatura
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
import time


class ContentExtractor:
    def __init__(self, save_content=True, main_save_path=None, logger=None, use_embeddings=False):
        """
        Initialize the content extractor system.

        :param save_content: Whether to save content or just display it (default is True).
        :param main_save_path: The main directory path where the content will be saved.
        :param logger: Logger instance for logging.
        :param use_embeddings: Whether to generate embeddings for the content (default is True).
        """
        self.main_save_path = main_save_path
        self.save_content = save_content
        self.logger = logger
        self.use_embeddings = use_embeddings  # Flag to enable or disable embeddings

        if self.use_embeddings:
            model_name = "BAAI/bge-large-en-v1.5"
            model_kwargs = {'device': 'cpu'}
            encode_kwargs = {'normalize_embeddings': True}
            self.hf_embeddings = HuggingFaceBgeEmbeddings(
                model_name=model_name,
                model_kwargs=model_kwargs,
                encode_kwargs=encode_kwargs
            )

    def generate_embedding(self, text):
        """
        Generate an embedding for the given text using the HuggingFace BGE model.

        :param text: The content text to embed.
        :return: Embedding of the text.
        """
        if self.use_embeddings:
            try:
                return self.hf_embeddings.embed_documents([text])[0]
            except Exception as e:
                self.logger.error(f"Error generating embeddings for {text}: {e}")
                return None
        else:
            return None  # If embeddings are disabled, return None

    def extract_youtube_link(self, soup):
        """
        Extract the YouTube link from an iframe if present in the HTML.

        :param soup: BeautifulSoup object of the webpage content.
        :return: YouTube video link if present, else None.
        """
        yt_iframe = soup.find("iframe")
        if yt_iframe and 'src' in yt_iframe.attrs:
            youtube_url = yt_iframe['src']
            if 'youtube' in youtube_url:
                return youtube_url
        return None

    def save_content_as_json(self, url, data, category, sub_category):
        """
        Save extracted content as a JSON file under the category/sub-category folder.

        :param url: URL of the scraped page.
        :param data: Extracted content to save.
        :param category: Category name.
        :param sub_category: Sub-category name.
        """
        try:
            cat_path = os.path.join(category, sub_category)

            if self.main_save_path:
                folder_path = os.path.join(self.main_save_path, cat_path)
            else:
                folder_path = cat_path

            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
                self.logger.info(f"Created folder structure: {folder_path}")

            title = data['title'].replace('/', '_').replace('\\', '_')
            if not title or title == "No Title Found":
                url_hash = hashlib.md5(url.encode()).hexdigest()
                file_name = f'{url_hash}.json'
            else:
                file_name = f'{title}.json'

            file_path = os.path.join(folder_path, file_name)

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
                print(f'Saved json to {file_path}')

        except Exception as e:
            print(f"Error saving content from {url}: {e}")
            self.logger.warning(f"Error saving content from {url}: {e}")

    def extract_content_from_html(self, url, html_content):
        """
        Extract and process the content from the HTML content of a URL.

        :param url: URL of the webpage.
        :param html_content: The fetched HTML content of the webpage.
        """
        try:
            start_extraction = time.time()
            content = trafilatura.extract(html_content)
            end_extraction = time.time()
            print(f'Extracted time for {url}: {end_extraction - start_extraction}')

            # Conditionally generate the embedding if enabled
            embedding = self.generate_embedding(content) if self.use_embeddings else None

            soup = BeautifulSoup(html_content, 'html.parser')

            category = soup.find("a", {"class": "category"})
            sub_category = soup.find("a", {"class": "channel"})
            header_title = soup.find("h1", {"class": "header-title"})

            category_text = category.text.strip() if category else "Uncategorized"
            sub_category_text = sub_category.text.strip() if sub_category else "General"
            header_title_text = header_title.text.strip() if header_title else "No Title Found"

            youtube_url = self.extract_youtube_link(soup)

            data = {
                "url": url,
                "category": category_text,
                "sub_category": sub_category_text,
                "title": header_title_text,
                "youtube_url": youtube_url,
                "content": content,
                "embedding": embedding  # Add embedding only if enabled
            }

            # For demonstration purposes, display the content
            if self.save_content:
                self.save_content_as_json(url, data, category_text, sub_category_text)
            else:
                print(f"--- Content from {url} ---")
                print(json.dumps(data, ensure_ascii=False, indent=4))

        except Exception as e:
            self.logger.error(f"Error extracting html for {url}: {e}")

if __name__ == '__main__':
    extractor = ContentExtractor(use_embeddings=False, main_save_path=None,save_content=False)
    start = time.time()
    url = "https://www.instructables.com/Tims-Mini-Plotter-2-With-Single-PCB/"
    try:
        response = requests.get(url)
        response.raise_for_status()
        html_content = response.text
    except Exception as e:
        print(f"Error extracting html for {url}: {e}")

    extractor.extract_content_from_html(url, html_content)
    end = time.time()
    print(f"Total Time taken to extract content from {url}: {end - start}")