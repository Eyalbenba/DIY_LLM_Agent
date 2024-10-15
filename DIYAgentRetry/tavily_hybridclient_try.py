import os
from dotenv import load_dotenv
from pymongo import MongoClient
from tavily import TavilyHybridClient

# Load environment variables from .env file
load_dotenv()

# Ensure the CO_API_KEY is available as an environment variable
cohere_api_key = os.getenv('CO_API_KEY')

# Check if the CO_API_KEY is loaded correctly
if not cohere_api_key:
    raise ValueError("CO_API_KEY is not set in the environment. Please check your .env file or environment setup.")

# Ensure CO_API_KEY is set in the environment
os.environ['CO_API_KEY'] = cohere_api_key


# Function to get the MongoDB client
def get_mongo_client(uri):
    return MongoClient(uri)


# Function for hybrid search
def hybrid_search_try(query):
    print("=== STAGE: Hybrid Search ===")

    # Load necessary environment variables
    uri = os.getenv('MongoURI')
    tavily_api_key = os.getenv('TAVILY_API_KEY')

    # Check if all necessary environment variables are loaded
    if not uri or not tavily_api_key:
        raise ValueError("MongoURI or TAVILY_API_KEY is not set in environment.")

    # Initialize MongoDB client and select database
    mongo_client = get_mongo_client(uri)
    db = mongo_client["all_scraped_data"]

    # Initialize Tavily Hybrid RAG Client
    hybrid_rag = TavilyHybridClient(
        api_key=tavily_api_key,
        db_provider="mongodb",
        collection=db.get_collection("all_data"),
        index="vector_index",
        embeddings_field="embedding",
        content_field="content"
    )

    # Perform the hybrid search
    results = hybrid_rag.search(query, max_local=5, max_foreign=2, save_foreign=True)

    return results


# Example usage
hybrid_rag_try = hybrid_search_try("jack-o-lantern")
print(hybrid_rag_try)
