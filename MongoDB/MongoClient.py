from pymongo import MongoClient
from datetime import datetime

class MongoDBClient:
    def __init__(self, uri, logger=None):
        """
        Initialize the MongoDB client for interacting with the databases.

        :param uri: MongoDB URI string for connection.
        :param logger: Logger for logging operations (optional).
        """
        self.client = MongoClient(uri)
        self.logger = logger or self.setup_default_logger()

        # Databases
        self.all_data_db = self.client["all_scraped_data"]
        self.chunks_db = self.client["chunks"]

    def setup_default_logger(self):
        import logging
        logger = logging.getLogger(__name__)
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        logger.addHandler(handler)
        return logger

    def save_full_data(self, data):
        """
        Save full scraped content to the 'all_data' collection in 'all_scraped_data' database.

        :param data: The scraped content data (dictionary).
        """
        try:
            collection = self.all_data_db["all_data_cohere"]
            data["created_at"] = datetime.utcnow()  # Add timestamp
            response = collection.insert_one(data)
            data_id = response.inserted_id
            self.logger.info(f"Successfully saved full data for URL: {data.get('url')}")
            return data_id
        except Exception as e:
            self.logger.error(f"Error saving full data: {e}")

    def save_chunk(self, chunk_data,content_id):
        """
        Save chunk data to a collection based on the category in the 'chunks' database.

        :param chunk_data: Dictionary containing the chunk data.
        """
        try:
            # Extract category from chunk data
            category = chunk_data.get('category')
            if not category:
                raise ValueError("Category not found in chunk_data")

            # Ensure category is a valid string for collection name
            collection_name = category.replace(" ", "_").lower()  # e.g., "Machine Learning" -> "machine_learning"

            # Access the collection based on the category
            collection = self.chunks_db[collection_name]

            # Add the content_id to the chunk data
            chunk_data["content_id"] = content_id

            # Add a timestamp for when the chunk was created
            chunk_data["created_at"] = datetime.utcnow()

            # Insert the chunk data into the collection
            collection.insert_one(chunk_data)
            self.logger.info(f"Successfully saved chunk data for : {chunk_data.get('title')} Chunk  #{chunk_data.get('chunk_index')}, URL: {chunk_data.get('url')}")
        except Exception as e:
            self.logger.error(f"Error saving chunk data for URL {chunk_data.get('url')}: {e}")

    def close(self):
        """
        Close the MongoDB connection.
        """
        self.client.close()
        self.logger.info("MongoDB connection closed.")