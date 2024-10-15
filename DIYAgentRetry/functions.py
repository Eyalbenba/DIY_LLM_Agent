# diy_agent/functions.py

from datetime import datetime, timezone
from typing import Dict
from DIYAgentRetry.AtlasClient import AtlasClient
from langchain.schema import SystemMessage
from langgraph.graph import END
from DIYAgentRetry.state import DIYAgentState, RefinedQuery, DIYPlan
from DIYAgentRetry.prompts import *
from DIYAgentRetry.utils import *
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.language_models import BaseChatModel
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage,HumanMessage , RemoveMessage
from pymongo import MongoClient
from tavily import TavilyHybridClient
import os
from dotenv import load_dotenv
import cohere
# You need to import or define the following:
# - TavilySearchResults: A class that handles web search functionality.
# - llm: The language model instance (e.g., OpenAI LLM).

def refine_user_query(state: DIYAgentState) -> Dict[str, str]:
    """Refine the user's query to make it clear and actionable."""
    print("=== STAGE: REFINE USER QUERY ===")
    user_query = state['user_query']
    state['messages'].append(HumanMessage(user_query,name="User"))
    llm = load_chat_model('gpt-3.5-turbo-0125')
    structured_llm = llm.with_structured_output(RefinedQuery)
    if not state['summary']:
        query_system_message = QUERY_SYSTEM_PROMPT.format(
            user_query=user_query,
            system_time=datetime.now(tz=timezone.utc).isoformat()
        )
    else:
        query_system_message = SECOND_QUERY_SYSTEM_PROMPT.format(
            user_query=user_query,
            system_time=datetime.now(tz=timezone.utc).isoformat(),
            user_feedback=state['human_refine_plan_string'],
            summary=state['summary'],

        )

    generated = structured_llm.invoke([SystemMessage(content=query_system_message)])

    state['messages'].append(AIMessage(f"Refined User Query : {generated.refined_query}", name="Bot"))
    # Update the state with the refined query
    return {"diy_query": generated.refined_query,"messages":state['messages']}

def generate_diy_plan(state: DIYAgentState) -> Dict[str, str]:
    """Generate the DIY plan based on the refined query and retrieved documents."""
    print("=== STAGE: Generate DIY Plan ===")
    diy_query = state['diy_query']
    retrieved_docs = state['retrieved_docs']
    llm = load_chat_model('gpt-4o')
    structured_llm = llm.with_structured_output(DIYPlan)

    summary = state.get("summary",'')
    if summary:
        diy_system_message = SECOND_DIYPLAN_SYSTEM_PROMPT.format(
            diy_query=diy_query,
            retrieved_docs="\n\n---\n\n".join(retrieved_docs),
            user_feedback=state['human_refine_plan_string'],
            summary=state['summary'],
            system_time=datetime.now(tz=timezone.utc).isoformat()
        )
    else:
        diy_system_message = DIYPLAN_SYSTEM_PROMPT.format(
            diy_query=diy_query,
            retrieved_docs="\n\n---\n\n".join(retrieved_docs),
            system_time=datetime.now(tz=timezone.utc).isoformat()
        )

    generated = structured_llm.invoke([SystemMessage(content=diy_system_message)])
    state['messages'].append(AIMessage(f"DIY Plan from the user query : {generated.plan}", name="Bot"))
    state['num_plans'] += 1
    # Update the state with the final plan
    return {"DIY_Final_Plan": generated.plan,"messages":state['messages']}

# def hybrid_search(state: DIYAgentState) -> Dict[str, str]:
#     print("=== STAGE: Hybrid Search ===")
#     search_query = state['diy_query']
#     uri = os.environ['MongoURI']
#     db = MongoClient(f"mongodb+srv://{uri}")["all_scraped_data"]
#
#     hybrid_rag = TavilyHybridClient(
#         api_key=os.environ['TAVILY_API_KEY'],
#         db_provider="mongodb",
#         collection=db.get_collection("all_data"),
#         index="vector_index",
#         embeddings_field="embedding",
#         content_field="content"
#     )
#     results = hybrid_rag.search(search_query, max_local=5, max_foreign=2,save_foreign=True)
def search_web(state: DIYAgentState) -> Dict[str, list]:
    """Retrieve documents from a web search based on the refined query."""
    print("=== STAGE: Web Search ===")
    search_query = state['diy_query']

    # Perform web search (You need to implement TavilySearchResults or replace it with a real search)
    tavily_search = TavilySearchResults(max_results=3,include_raw_content=True)
    search_docs = tavily_search.invoke(search_query)

    # Format the retrieved documents
    formatted_search_docs = [
        f'<Document href="{doc["url"]}"/>\n{doc["content"]}\n</Document>'
        for doc in search_docs
    ]

    # Update the state with the retrieved documents
    return {"retrieved_docs": formatted_search_docs}

def search_mongo_db(state: DIYAgentState) -> Dict[str, list]:
    mongo_uri = os.getenv('MONGO_URI')
    db_name = "all_scraped_data"
    collection_name = "all_data"
    index_name = "vector_index"  # Replace this with your actual vector index name
    attr_name = "embedding"  # Replace this with the field name that holds the embeddings

    # Step 2: Initialize AtlasClient with URI and database name
    atlas_client = AtlasClient(atlas_uri=mongo_uri, dbname=db_name)

    try:
        atlas_client.ping()
        print("Successfully connected to MongoDB Atlas!")
    except Exception as e:
        print(f"Connection failed: {e}")
        return

        # Step 4: Embed the query using Cohere
    try:
        query = state['diy_query']
        # print(f"Generating embedding for query: '{query}'")
        embedding_vector = cohere_embed([query])[0]  # Get the embedding for the query
    except Exception as e:
        print(f"Embedding generation failed: {e}")
        return

        # Step 5: Perform vector search for "jack-o-lantern"
    try:
        print(f"Performing vector search for {query}...")
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
    # Step 2: Initialize AtlasClient with URI and database name
    atlas_client = AtlasClient(atlas_uri=mongo_uri, dbname=db_name)
def max_plans_reached(state: DIYAgentState):
    print("=== STAGE: Checking If Max Plans Reached ===")
    num_plans = state['num_plans']
    if num_plans >= 2:
        return END
    return "human_feedback_on_diyplan"
def human_feedback_on_diyplan(state: DIYAgentState):
    """ Getting Feedback from user on DIY Plan """
    pass
def should_make_new_diy_plan(state: DIYAgentState):
    print("=== STAGE: Should Make New Diy Plan ===")
    human_feedback_on_diy = state['human_refine_plan_string']
    if human_feedback_on_diy:
        return "summarize_conversation"
    return END
def summarize_conversation(state: DIYAgentState) -> Dict[str, list]:
    print("=== STAGE: Summarize Conversationn ===")

    human_feedback_on_diy = state['human_refine_plan_string']
    first_diy_plan = state['DIY_Final_Plan']
    summary_insruction = SUMMARY_INSTRUCTION.format(diy_plan=first_diy_plan,user_feedback=human_feedback_on_diy)
    model = load_chat_model('gpt-4o')
    response = model.invoke(summary_insruction)

    #Delete all but the two last messages
    delete_messages = [RemoveMessage(id =m.id) for m in state['messages'][:-3]]
    return {"summary":response.content,"messages": delete_messages}

# def should_summarize(state: DIYAgentState):
#     messages = state.get("messages",[])
#     if len(messages) >= 5:
#         return "summarize_conversation"
#     return blabla







def hybrid_search_try(query):
    print("=== STAGE: Hybrid Search ===")

    # Load the MongoDB URI and TAVILY_API_KEY from environment
    uri = os.getenv('MongoURI')
    tavily_api_key = os.getenv('TAVILY_API_KEY')

    # Check if the necessary environment variables are loaded
    if not uri or not tavily_api_key:
        raise ValueError("MongoURI or TAVILY_API_KEY not set in environment.")

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


