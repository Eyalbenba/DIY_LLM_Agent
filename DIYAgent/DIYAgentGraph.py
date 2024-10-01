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



class GenerateAgentState(TypedDict):
    name: str
    plan: str
    human_feedback:str

def human_feedback(state:GenerateAgentState):
    pass
def should_continue(state: GenerateAgentState):
    human_feedback = state.get('human_feedback',None)
    if human_feedback:
        return "implement_plan"

    return END


def search_web(state: DIYAgentState):
    """ Retrieve docs from web search """

    # Search query
    structured_llm = llm.with_structured_output(SearchQuery)
    search_query = structured_llm.invoke([search_instructions] + state['messages'])

    # Search
    search_docs = tavily_search.invoke(search_query.search_query)

    # Format
    formatted_search_docs = "\n\n---\n\n".join(
        [
            f'<Document href="{doc["url"]}"/>\n{doc["content"]}\n</Document>'
            for doc in search_docs
        ]
    )

    return {"retrieved_docs": [formatted_search_docs]}


def get_user_query(state: DIYAgentState):
    # Capture user input as a query
    user_input = input("Tell me about your DIY project: ")

    # Add the user's query as a new HumanMessage to the sequence of messages
    new_message = HumanMessage(content=user_input)

    # Create a new sequence with the added message (since sequences are immutable)
    state.messages = state.messages + [new_message]

    # Optionally, if you're storing user_query separately
    state.user_query = user_input




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
            ("placeholder", "{queries}"),
        ]
    )

    # Load the query processing model defined in the configuration
    model = load_chat_model(configuration.query_model).with_structured_output(SearchQuery)

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
    generated = cast(SearchQuery, await model.ainvoke(message_value, config))

    # Return the generated query in the expected format
    return {
        "queries": [generated.query],
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
    generated = cast(DIYPlan, await model.ainvoke(message_value, config))

    # Return the generated query in the expected format
    return {
        "DIY_Final_Plan": [generated.plan],
    }

async def generate_diy_plan(state: DIYAgentState ,*, config: RunnableConfig) -> dict[str, list[str]]:
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
    generated = cast(SearchQuery, await model.ainvoke(message_value, config))

    # Return the generated query in the expected format
    return {
        "websearch_query": [generated.query],
    }


builder = StateGraph(DIYAgentState)
builder.add_node("get_user_query",get_user_query)
builder.add_node("refine_user_query",refine_user_query)
builder.add_node("human_feedback", human_feedback)
builder.add_node("generate_search_query",generate_search_query)
builder.add_node("RAG_docs", search_web)
builder.add_node("generate_diy_plan",generate_diy_plan)

# Add nodes and edges
# builder = StateGraph(GenerateAnalystsState)
# builder.add_node("create_analysts", create_analysts)
# builder.add_node("human_feedback", human_feedback)
# builder.add_edge(START, "create_analysts")
# builder.add_edge("create_analysts", "human_feedback")
# builder.add_conditional_edges("human_feedback", should_continue, ["create_analysts", END])
#
# # Compile
# memory = MemorySaver()
# graph = builder.compile(interrupt_before=['human_feedback'], checkpointer=memory)
#
# # View
# display(Image(graph.get_graph(xray=1).draw_mermaid_png()))