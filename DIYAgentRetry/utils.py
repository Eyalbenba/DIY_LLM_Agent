import cohere
from dotenv import load_dotenv
import os
from pymongo import MongoClient
from langchain_core.language_models import BaseChatModel

# Load environment variables from .env file
load_dotenv()

# Initialize the Cohere client
co = cohere.Client(os.getenv('CO_API_KEY'))
def cohere_embed(texts, type='search_query'):
    return co.embed(
        model='embed-english-v3.0',
        texts=texts,
        input_type=type
    ).embeddings

def get_mongo_client(uri):
    """Initialize and return a MongoDB client."""
    return MongoClient(uri)


def load_chat_model(fully_specified_name: str) -> BaseChatModel:
    """Load a chat model from a fully specified name.

    Args:
        fully_specified_name (str): String in the format 'provider/model'.
    """
    if "/" in fully_specified_name:
        provider, model = fully_specified_name.split("/", maxsplit=1)
    else:
        provider = ""
        model = fully_specified_name
    return init_chat_model(model, model_provider=provider)