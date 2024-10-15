import requests
from bs4 import BeautifulSoup
import os
import json
import hashlib
import trafilatura
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
import time
import cohere
from dotenv import load_dotenv
import asyncio
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lex_rank import LexRankSummarizer
import nltk
import uuid
from transformers import GPT2TokenizerFast
nltk.download('punkt_tab')
nltk.download('punkt')

load_dotenv()

# Initialize the Cohere client
co = cohere.ClientV2(os.getenv('CO_API_PROD_KEY'))

class ContentExtractor:
    def __init__(self, mongo_client,save_content=True, main_save_path=None, logger=None, use_embeddings=True):
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
        self.mongo_client = mongo_client  # MongoDB client to store data
        self.tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")
        if self.use_embeddings:
            # model_name = "BAAI/bge-large-en-v1.5"
            # model_kwargs = {'device': 'cpu'}
            # encode_kwargs = {'normalize_embeddings': True}
            # self.hf_embeddings = HuggingFaceBgeEmbeddings(
            #     model_name=model_name,
            #     model_kwargs=model_kwargs,
            #     encode_kwargs=encode_kwargs
            # )
            self.cohere_api_embed = co

    def generate_summary_text_lexrank(self, text, url, sentence_count=5):
        """
        Summarizes the provided text using LexRank algorithm and logs any errors with the associated URL.

        Args:
        - text (str): The text to be summarized.
        - url (str): The URL from which the text was extracted.
        - sentence_count (int): Number of sentences for the summary.

        Returns:
        - str: The summarized text.
        """
        try:
            # Parse the text using PlaintextParser and Tokenizer
            parser = PlaintextParser.from_string(text, Tokenizer("english"))

            # Initialize LexRank summarizer
            summarizer = LexRankSummarizer()

            # Generate the summary
            summary = summarizer(parser.document, sentence_count)

            # Combine the summary sentences into a single string
            summary_text = " ".join([str(sentence) for sentence in summary])

            return summary_text
        except Exception as e:
            self.logger.error(f"Error generating summary for the text from URL {url}: {e}")
            return None

    def generate_embedding_hf(self, text):
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

    def generate_embedding_co(self, text,url, data_type=float, sleep_time=0.05, summary=False,chunk=False):
        """
        Generate an embedding for the given text with a sleep delay to avoid exceeding API limits.

        Args:
        - text (str): The text to be embedded.
        - data_type (type): The data type for the embeddings (default: float).
        - sleep_time (float): Time to sleep between API calls, in seconds (default: 0.6s to ensure < 100 calls per minute).

        Returns:
        - embedding: The generated embedding or None if an error occurs.
        """
        if self.use_embeddings:
            try:
                # Sleep to ensure we don't exceed API rate limits

                res = self.cohere_api_embed.embed(texts=[text], \
                                                  model="embed-english-light-v3.0", \
                                                  input_type="search_document", \
                                                  embedding_types=["float"])
                time.sleep(sleep_time)
                return res.embeddings.float[0]
            except Exception as e:
                # Log based on whether it's a summary or a chunk
                if summary and chunk:
                    self.logger.error(f"Error generating summary and chunk embeddings for {url}: {e}")
                elif summary:
                    self.logger.error(f"Error generating summary embeddings for {url}: {e}")
                elif chunk:
                    self.logger.error(f"Error generating chunk embeddings for {url}: {e}")
                else:
                    self.logger.error(f"Error generating embeddings for {url}: {e}")
        else:
            return None  # If embeddings are disabled, return None

    def chunk_content_and_generate_embeddings(self, url,category,sub_category ,title,content, max_tokens=512):
        """
        Split content into chunks of max_tokens length, preserving sentence boundaries.
        Generate embeddings for each chunk and return the embeddings and the start/end pointers.

        Returns a list of chunk embeddings and their corresponding start and end token positions.
        """
        sentences = nltk.sent_tokenize(content)
        current_chunk = []
        current_length = 0
        start_token_pos = 0
        chunk_index=1
        chunks_info = []

        for idx,sentence in enumerate(sentences):
            tokenized_sentence = self.tokenizer.tokenize(sentence)
            sentence_length = len(tokenized_sentence)

            # If adding the next sentence exceeds the max token limit, finalize the current chunk
            if current_length + sentence_length > max_tokens:
                chunk_text = " ".join(current_chunk)
                embedding = self.generate_embedding_co(chunk_text, url,chunk=True)
                chunks_info.append({
                    "url": url,
                    "category": category,
                    "sub_category": sub_category,
                    "title": title,
                    "start_pointer": start_token_pos,
                    "end_pointer": start_token_pos + current_length,
                    "embedding": embedding,
                    "chunk_index":chunk_index
                })
                # Reset for the next chunk
                current_chunk = []
                start_token_pos += current_length
                current_length = 0
                chunk_index+=1


            current_chunk.append(sentence)
            current_length += sentence_length

        # Add any remaining chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            embedding = self.generate_embedding_co(chunk_text, url,chunk=True)
            chunks_info.append({
                "url": url,
                    "category": category,
                    "sub_category": sub_category,
                    "title": title,
                    "start_pointer": start_token_pos,
                    "end_pointer": start_token_pos + current_length,
                    "embedding": embedding,
                    "chunk_index": chunk_index
            })

        return chunks_info

    def save_chunk_as_json(self, chunk_data, category, sub_category):
        """
        Save each chunk as a JSON file under the category_chunk/sub-category folder.

        :param chunk_data: Dictionary containing chunk info (url, title, embedding, etc.).
        :param category: Category name.
        :param sub_category: Sub-category name.
        """
        try:
            # Define the folder path for saving chunk files under category_chunk/sub-category
            cat_chunk_path = os.path.join(f"{category}_chunk", sub_category)

            # If a main save path exists, use it; otherwise, default to current folder
            if self.main_save_path:
                folder_path = os.path.join(self.main_save_path, cat_chunk_path)
            else:
                folder_path = cat_chunk_path

            # Create the folder structure if it doesn't exist
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
                self.logger.info(f"Created chunk folder structure: {folder_path}")

            # Replace invalid characters in the title and handle missing titles
            title = chunk_data['title'].replace('/', '_').replace('\\', '_')
            if not title or title == "No Title Found":
                url_hash = hashlib.md5(chunk_data['url'].encode()).hexdigest()
                base_file_name = f'{url_hash}'
            else:
                base_file_name = f'{title}'

            # Ensure that each chunk has a unique index (1, 2, 3, etc.)
            chunk_index = chunk_data.get("chunk_index", str(uuid.uuid4()))  # Default index is 1 if not provided
            file_name = f"{base_file_name}_{chunk_index}.json"

            # Define the full file path
            file_path = os.path.join(folder_path, file_name)

            # Save the chunk data as a JSON file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(chunk_data, f, ensure_ascii=False, indent=4)
                print(f'Saved chunk json to {file_path}')
                self.logger.info(f"Saved chunk json {file_name} to {file_path}")

        except Exception as e:
            print(f"Error saving chunk from {chunk_data['url']}: {e}")
            self.logger.warning(f"Error saving chunk from {chunk_data['url']}: {e}")

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
            # print(f'Extracted time for {url}: {end_extraction - start_extraction}')

            # Conditionally generate the embedding if enabled
            soup = BeautifulSoup(html_content, 'html.parser')

            category = soup.find("a", {"class": "category"})
            sub_category = soup.find("a", {"class": "channel"})
            header_title = soup.find("h1", {"class": "header-title"})

            category_text = category.text.strip() if category else "Uncategorized"
            sub_category_text = sub_category.text.strip() if sub_category else "General"
            header_title_text = header_title.text.strip() if header_title else "No Title Found"

            # content_embedding = self.generate_embedding_co(content, url) if self.use_embeddings else None
            summary = self.generate_summary_text_lexrank(content, url)
            summary_embedding = self.generate_embedding_co(summary, url, summary=True) if summary else None
            chunks_data = self.chunk_content_and_generate_embeddings(url,category_text,sub_category_text ,header_title_text,content)
            youtube_url = self.extract_youtube_link(soup)

            data = {
                "url": url,
                "category": category_text,
                "sub_category": sub_category_text,
                "title": header_title_text,
                "youtube_url": youtube_url,
                "content": content,
                # "content_embedding": content_embedding,  # Add embedding only if enabled,
                "summary": summary,
                "summary_embedding": summary_embedding

            }

            # For demonstration purposes, display the content
            if self.save_content:
                content_id = self.mongo_client.save_full_data(data)
                for chunk in chunks_data:
                    self.mongo_client.save_chunk(chunk,content_id)
            else:
                print(f"--- Content from {url} ---")
                print(json.dumps(data, ensure_ascii=False, indent=4))

        except Exception as e:
            self.logger.error(f"Error extracting html for {url}: {e}")