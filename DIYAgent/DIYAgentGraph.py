from pydantic import BaseModel
from IPython.display import display , Image
from langgraph.graph import START,END,StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage,HumanMessage,SystemMessage
from langchain_core.runnables import RunnableConfig, ensure_config
from typing import TypedDict
from DIYAgent.states import *
from DIYAgent.utils import *
from datetime import datetime, timezone
from typing import cast
from DIYAgent.config import *
from langchain_core.documents import Document
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.tools.tavily_search import TavilySearchResults


class GenerateAgentState(TypedDict):
    name: str
    plan: str
    human_feedback:str

async def human_feedback(state:GenerateAgentState):
    pass
async def should_continue(state: DIYAgentState):
    human_feedback = state.get('human_feedback_string',None)
    if human_feedback:
        return
    return


async def search_web(state: DIYAgentState):
    """ Retrieve docs from web search """

    # Search query
    search_query = state.search_query

    # Search
    tavily_search = TavilySearchResults(max_results=3)
    search_docs = tavily_search.invoke(search_query)

    # Format
    formatted_search_docs = "\n\n---\n\n".join(
        [
            f'<Document href="{doc["url"]}"/>\n{doc["content"]}\n</Document>'
            for doc in search_docs
        ]
    )

    return {"retrieved_docs": [formatted_search_docs]}


async def get_user_query(state: DIYAgentState):
    print("Waiting for user input...")
    # Capture user input as a query
    user_input = input("Tell me about your DIY project: ")
    print("User input received:", user_input)

    # Add the user's query as a new HumanMessage to the sequence of messages
    new_message = HumanMessage(content=user_input)
    state.messages = state.messages + [new_message]

    state.user_query = user_input
    print("Updated state with user query:", state)
    return {'user_query': user_input}



async def refine_user_query(
        state: DIYAgentState, *, config: RunnableConfig
) -> dict[str, list[str]]:
    """Generate a search query based on the current state and configuration.

    This function analyzes the messages in the state and generates an appropriate
    search query by always using the language model to refine the query, even if
    it's the first user input.

    Args:
        state (DIYAgentState): The current state containing messages and other information.
        config (RunnableConfig | None, optional): Configuration for the query generation process.

    Returns:
        dict[str, list[str]]: A dictionary with a 'queries' key containing a list of generated queries.

    Behavior:
        - For any number of messages, it uses a language model to refine the query.
        - The function uses the configuration to set up the prompt and model for query generation.
    """
    # Load the configuration specific to the DIYAgent
    configuration = DIYAgentConfiguration.from_runnable_config(config)

    # Construct a prompt using the query_system_prompt from the configuration
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", configuration.query_system_prompt),  # System prompt for query refinement
            ("placeholder", "{user_query}"),
        ]
    )

    # Load the query processing model defined in the configuration
    model = load_chat_model(configuration.query_model).with_structured_output(SearchQuery)

    # Prepare the input data for the model invocation
    message_value = await prompt.ainvoke(
        {
            "messages": state.messages,  # Pass all messages for context, even if it's just one
            "user_query": state.user_query,  # Combine existing queries if available
            "system_time": datetime.now(tz=timezone.utc).isoformat(),  # Current time in UTC
        },
        config,
    )

    # Use the model to generate a refined query
    generated = cast(SearchQuery, await model.ainvoke(message_value, config))

    # Return the generated query in the expected format
    return {
        "queries": [generated.search_query],
    }

async def generate_search_query(state: DIYAgentState,*, config: RunnableConfig) -> dict[str, list[str]]:
    # Load the configuration specific to the DIYAgent
    configuration = DIYAgentConfiguration.from_runnable_config(config)

    # Construct a prompt using the query_system_prompt from the configuration
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", configuration.search_system_prompt),  # System prompt for query refinement
            ("placeholder", "{docs}"),
        ]
    )
    # Load the query processing model defined in the configuration
    model = load_chat_model(configuration.search_query_model).with_structured_output(SearchQuery)

    # Prepare the input data for the model invocation
    message_value = await prompt.ainvoke(
        {
            "messages": state.messages,  # Pass all messages for context, even if it's just one
            "queries": "\n- ".join(state.queries) if state.queries else "",  # Combine existing queries if available
            "docs":state.retrieved_docs,
            "system_time": datetime.now(tz=timezone.utc).isoformat(),  # Current time in UTC
        },
        config,
    )

    # Use the model to generate a refined query
    generated = cast(SearchQuery, await model.ainvoke(message_value, config))

    # Return the generated query in the expected format
    return {
        "search_query": [generated.search_query],
    }

async def generate_diy_plan(state: DIYAgentState ,*, config: RunnableConfig) -> OutputState:
    # Load the configuration specific to the DIYAgent
    configuration = DIYAgentConfiguration.from_runnable_config(config)

    # Construct a prompt using the query_system_prompt from the configuration
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", configuration.diyplan_system_prompt),  # System prompt for query refinement
            ("placeholder", "{queries}"),
        ]
    )
    # Load the query processing model defined in the configuration
    model = load_chat_model(configuration.search_query_model).with_structured_output(SearchQuery)

    # Prepare the input data for the model invocation
    message_value = await prompt.ainvoke(
        {
            "messages": state.messages,  # Pass all messages for context, even if it's just one
            "queries": "\n- ".join(state.queries) if state.queries else "",  # Combine existing queries if available
            "system_time": datetime.now(tz=timezone.utc).isoformat(),  # Current time in UTC
        },
        config,
    )

    # Use the model to generate a refined query
    generated = cast(DIYPlan, await model.ainvoke(message_value, config))

    # Return the generated query in the expected format
    return {
        "DIY_Final_Plan": [generated.plan],
    }


def build_diy_graph():
    # Initialize the StateGraph builder with DIYAgentState as the context
    builder = StateGraph(DIYAgentState)

    # Add nodes (representing states in the agent's workflow)
    builder.add_node("get_user_query", get_user_query)
    builder.add_node("refine_user_query", refine_user_query)
    builder.add_node("human_feedback", human_feedback)
    builder.add_node("generate_search_query", generate_search_query)
    builder.add_node("RAG_docs", search_web)
    builder.add_node("generate_diy_plan", generate_diy_plan)

    # Define transitions (edges between states)
    builder.add_edge(START, "get_user_query")  # Start -> Get user's query
    builder.add_edge("get_user_query", "refine_user_query")  # Get user's query -> Refine query
    builder.add_edge("refine_user_query", "human_feedback")  # Refine query -> Human feedback

    # Add conditional transitions based on human feedback
    builder.add_conditional_edges("human_feedback", should_continue, ['generate_search_query', 'get_user_query'])

    # Continue transitions after conditional step
    builder.add_edge("generate_search_query", "RAG_docs")  # Generate search query -> Retrieve docs
    builder.add_edge("RAG_docs", "generate_diy_plan")  # Retrieve docs -> Generate DIY plan

    # Set up memory saving for checkpointing the state graph
    memory = MemorySaver()

    # Compile the state graph with interrupt handling at the 'human_feedback' step
    graph = builder.compile(interrupt_before=['human_feedback'], checkpointer=memory)

    # Return the compiled graph object
    return graph



