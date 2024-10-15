# diy_agent/graph.py

from langgraph.graph import StateGraph, START, END
from DIYAgentRetry.state import DIYAgentState
from DIYAgentRetry.functions import refine_user_query, search_web, generate_diy_plan,summarize_conversation,human_feedback_on_diyplan,should_make_new_diy_plan,max_plans_reached

def build_graph():
    """Build the state graph for the DIY Agent."""
    builder = StateGraph(DIYAgentState)

    # Add nodes to the graph
    builder.add_node("refine_user_query", refine_user_query)
    builder.add_node("search_web", search_web)
    builder.add_node("generate_diy_plan", generate_diy_plan)
    builder.add_node("human_feedback_on_diyplan", human_feedback_on_diyplan)
    builder.add_node("summarize_conversation",summarize_conversation)

    # Define edges between nodes
    builder.add_edge(START, "refine_user_query")
    builder.add_edge("refine_user_query", "search_web")
    builder.add_edge("search_web", "generate_diy_plan")
    builder.add_conditional_edges("generate_diy_plan",max_plans_reached, ["human_feedback_on_diyplan",END])
    builder.add_conditional_edges("human_feedback_on_diyplan",should_make_new_diy_plan, ["summarize_conversation",END])
    builder.add_edge("summarize_conversation", "refine_user_query")
    ## Need to add how to continue after summarize of the conversation


    return builder
