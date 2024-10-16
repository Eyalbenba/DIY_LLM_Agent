import os
from dotenv import load_dotenv
from pymongo import MongoClient
import cohere

# Load environment variables from .env file
load_dotenv()
from tavily import TavilyHybridClient
# Ensure the CO_API_KEY is available as an environment variable
# cohere_api_key = os.getenv('CO_API_PROD_KEY')

# Check if the CO_API_KEY is loaded correctly
# if not cohere_api_key:
#     raise ValueError("CO_API_KEY is not set in the environment. Please check your .env file or environment setup.")

# Ensure CO_API_KEY is set in the environment
# os.environ['CO_API_PROD_KEY'] = cohere_api_key
co = cohere.ClientV2(os.getenv('CO_API_KEY'))


# Function to get the MongoDB client
def get_mongo_client(uri):
    return MongoClient(uri)
# embedding_function: function (optional) - A custom embedding function (if you want to use one). The function MUST take in a str and return a list[float]. If no function is provided, defaults to Cohere's Embed. Keep in mind that you shouldn't mix different embeddings in the same database collection.
# res = self.cohere_api_embed.embed(texts=[text], \
#                                                   model="embed-english-light-v3.0", \
#                                                   input_type="search_document", \
#                                                   embedding_types=["float"])
#                 time.sleep(sleep_time)
#                 return res.embeddings.float[0]
def my_embedding_function(text:str,search_type) -> list[float]:
    res = co.embed(texts=text, \
            model="embed-english-light-v3.0", \
            input_type=search_type, \
            embedding_types=["float"])
    return_value = res.embeddings.float
    return return_value

# Function for hybrid search
def hybrid_search_try(query):
    print("=== STAGE: Hybrid Search ===")

    # Load necessary environment variables
    uri = os.getenv('MONGO_URI')
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
        collection=db.get_collection("all_data_cohere"),
        index="vector_index",
        embeddings_field="summary_embedding",
        embedding_function=my_embedding_function,
        content_field="content"
    )

    # Perform the hybrid search
    results = hybrid_rag.search(query, max_local=5, max_foreign=2)

    return results


# Example usage
hybrid_rag_try = hybrid_search_try("Variable Power Supply")
for result in hybrid_rag_try:
    print(result)
