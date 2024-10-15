import os
from dotenv import load_dotenv
from pymongo import MongoClient
import cohere
# Load environment variables from .env file
load_dotenv()

# Initialize the Cohere client
co = cohere.Client(os.getenv('CO_API_KEY'))

class AtlasClient:
    def __init__(self, atlas_uri, dbname):
        self.mongodb_client = MongoClient(atlas_uri)
        self.database = self.mongodb_client[dbname]

    # A quick way to test if we can connect to Atlas instance
    def ping(self):
        self.mongodb_client.admin.command('ping')

    def get_collection(self, collection_name):
        collection = self.database[collection_name]
        return collection

    def find(self, collection_name, filter={}, limit=10):
        collection = self.database[collection_name]
        items = list(collection.find(filter=filter, limit=limit))
        return items

    # Vector search functionality
    def vector_search(self, collection_name, index_name, attr_name, embedding_vector, limit=5):
        collection = self.database[collection_name]
        results = collection.aggregate([
            {
                '$vectorSearch': {
                    "index": index_name,
                    "path": attr_name,
                    "queryVector": embedding_vector,
                    "numCandidates": 50,
                    "limit": limit,
                }
            },
            {
                "$project": {
                '_id': 0,
                'url': 1,               # Include URL
                'category': 1,           # Include Category
                'sub_category': 1,       # Include Sub-category
                'title': 1,              # Include Title
                'content': 1,            # Include Content
                'search_score': {"$meta": "vectorSearchScore"}  # Include Search Score
                }
            }
        ])
        return list(results)

    def close_connection(self):
        self.mongodb_client.close()

def _cohere_embed(texts, type='search_query'):
    return co.embed(
        model='embed-english-v3.0',
        texts=texts,
        input_type=type
    ).embeddings



# Main function to execute vector search query
def main():
    # Step 1: Load MongoDB URI from .env file
    load_dotenv()
    mongo_uri = os.getenv('MONGO_URI')
    db_name = "all_scraped_data"
    collection_name = "all_data"
    index_name = "vector_index"  # Replace this with your actual vector index name
    attr_name = "embedding"  # Replace this with the field name that holds the embeddings

    # Step 2: Initialize AtlasClient with URI and database name
    atlas_client = AtlasClient(atlas_uri=mongo_uri, dbname=db_name)

    # Step 3: Ping to check if the connection works
    try:
        atlas_client.ping()
        print("Successfully connected to MongoDB Atlas!")
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    # Step 4: Embed the query using Cohere
    try:
        query = "jack-o-lantern"
        print(f"Generating embedding for query: '{query}'")
        embedding_vector = _cohere_embed([query])[0]  # Get the embedding for the query
    except Exception as e:
        print(f"Embedding generation failed: {e}")
        return

    # Step 5: Perform vector search for "jack-o-lantern"
    try:
        print("Performing vector search for 'jack-o-lantern'...")
        results = atlas_client.vector_search(collection_name=collection_name,
                                             index_name=index_name,
                                             attr_name=attr_name,
                                             embedding_vector=embedding_vector,
                                             limit=5)

        # Step 6: Print the results
        if results:
            print("Search Results:")
            for result in results:
                print(result)
        else:
            print("No results found for the query.")

    except Exception as e:
        print(f"Vector search failed: {e}")

    # Step 7: Close the connection after you're done
    atlas_client.close_connection()




# Entry point for the program
if __name__ == "__main__":
    main()
