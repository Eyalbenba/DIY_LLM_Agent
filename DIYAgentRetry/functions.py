# diy_agent/functions.py

from datetime import datetime, timezone
from typing import Dict
from langchain.schema import SystemMessage
from langgraph.graph import END
from DIYAgentRetry.state import DIYAgentState, RefinedQuery, DIYPlan
from DIYAgentRetry.prompts import QUERY_SYSTEM_PROMPT, DIYPLAN_SYSTEM_PROMPT
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.language_models import BaseChatModel
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage,HumanMessage , RemoveMessage
# You need to import or define the following:
# - TavilySearchResults: A class that handles web search functionality.
# - llm: The language model instance (e.g., OpenAI LLM).

def refine_user_query(state: DIYAgentState) -> Dict[str, str]:
    """Refine the user's query to make it clear and actionable."""
    print("Starting Refine User Query")
    user_query = state['user_query']
    state['messages'].append(HumanMessage(user_query,name="User"))
    llm = load_chat_model('gpt-3.5-turbo-0125')
    structured_llm = llm.with_structured_output(RefinedQuery)

    query_system_message = QUERY_SYSTEM_PROMPT.format(
        user_query=user_query,
        system_time=datetime.now(tz=timezone.utc).isoformat()
    )

    generated = structured_llm.invoke([SystemMessage(content=query_system_message)])

    state['messages'].append(AIMessage(f"Refined User Query : {generated.refined_query}", name="Bot"))
    # Update the state with the refined query
    return {"diy_query": generated.refined_query,"messages":state['messages']}

def generate_diy_plan(state: DIYAgentState) -> Dict[str, str]:
    """Generate the DIY plan based on the refined query and retrieved documents."""
    print("Starting Generate DIY Plan")
    diy_query = state['diy_query']
    retrieved_docs = state['retrieved_docs']
    llm = load_chat_model('gpt-3.5-turbo-0125')
    structured_llm = llm.with_structured_output(DIYPlan)

    summary = state.get("summary",'')
    if summary:
        pass
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


def search_web(state: DIYAgentState) -> Dict[str, list]:
    """Retrieve documents from a web search based on the refined query."""
    print("Starting Web Search")
    search_query = state['diy_query']

    # Perform web search (You need to implement TavilySearchResults or replace it with a real search)
    tavily_search = TavilySearchResults(max_results=5,include_raw_content=True)
    search_docs = tavily_search.invoke(search_query)

    # Format the retrieved documents
    formatted_search_docs = [
        f'<Document href="{doc["url"]}"/>\n{doc["content"]}\n</Document>'
        for doc in search_docs
    ]

    # Update the state with the retrieved documents
    return {"retrieved_docs": formatted_search_docs}

def max_plans_reached(state: DIYAgentState):
    num_plans = state['num_plans']
    if num_plans >= 2:
        return END
    return "human_feedback_on_diyplan"
def human_feedback_on_diyplan(state: DIYAgentState):
    """ Getting Feedback from user on DIY Plan """
    pass
def should_make_new_diy_plan(state: DIYAgentState):
    human_feedback_on_diy = state['human_refine_plan_string']
    if human_feedback_on_diy:
        return "summarize_conversation"
    return END
def summarize_conversation(state: DIYAgentState) -> Dict[str, list]:
    summary = state.get("summary","")
    if summary:
        summary_message= (f"This is the summary of the conversation up to now {summary} \n\n"
                          "Extend the summary taking into account the new messages above:"
        )
    else:
        summary_message = "Create a summary of the conversation above:"
    messages = state.get("messages",[]) + [HumanMessage(summary_message,name="User")]
    model = load_chat_model('gpt-3.5-turbo-0125')
    response = model.invoke(messages)

    #Delete all but the two last messages
    delete_messages = [RemoveMessage(id =m.id) for m in state['messages'][:-3]]
    return {"summary":response.content,"messages": delete_messages}

def should_summarize(state: DIYAgentState):
    messages = state.get("messages",[])
    if len(messages) >= 5:
        return "summarize_conversation"
    return blabla
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
