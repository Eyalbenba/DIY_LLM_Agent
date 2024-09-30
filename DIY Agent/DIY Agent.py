from pydantic import BaseModel
from IPython.display import display , Image
from langgraph.graph import START,END,StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage,HumanMessage,SystemMessage
from typing import TypedDict
class DIYAgent(BaseModel):
    name: str
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

def create_diy_agent(state:GenerateAgentState):
    name = state.get('name')
    plan = state.get('plan')
    human_feedback = state.get('human_feedback',None)
    llm = llm.

builder = StateGraph(GenerateAgentState)
builder.add_node("create_diy_agent")