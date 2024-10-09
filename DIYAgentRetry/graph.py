# diy_agent/graph.py

from langgraph.graph import StateGraph, START, END
from DIYAgentRetry.state import DIYAgentState
from DIYAgentRetry.functions import refine_user_query, search_web, generate_diy_plan

def build_graph():
    """Build the state graph for the DIY Agent."""
    builder = StateGraph(DIYAgentState)

    # Add nodes to the graph
    builder.add_node("refine_user_query", refine_user_query)
    builder.add_node("search_web", search_web)
    builder.add_node("generate_diy_plan", generate_diy_plan)

    # Define edges between nodes
    builder.add_edge(START, "refine_user_query")
    builder.add_edge("refine_user_query", "search_web")
    builder.add_edge("search_web", "generate_diy_plan")
    builder.add_edge("generate_diy_plan", END)

    return builder
