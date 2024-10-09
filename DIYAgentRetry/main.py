# diy_agent/main.py

from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from DIYAgentRetry.graph import build_graph
from DIYAgentRetry.state import DIYAgentState
import os
import getpass
from dotenv import load_dotenv
import os
from dotenv import load_dotenv


def main():
    # Load environment variables from .env file
    load_dotenv()
    os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
    os.environ['TAVILY_API_KEY'] = os.getenv('TAVILY_API_KEY')

    # Build the graph
    builder = build_graph()
    memory = MemorySaver()
    graph = builder.compile(checkpointer=memory)

    # Get user query input
    user_query = input("What do you want to build? \n")

    # Initialize the agent's state
    diystate = DIYAgentState(
        user_query=user_query,
        messages=[],
        human_feedback_string='',
        diy_query='',
        DIY_Final_Plan='',
        retrieved_docs=[]
    )

    thread = {"configurable": {"thread_id": "13"}}

    # Run the graph to generate the DIY plan
    for chunk in graph.stream(diystate,config=thread,stream_mode="updates"):
        print(chunk)
    # graph_run = graph.invoke(diystate, thread)

    # Output the initial DIY plan
    # print("DIY Final Plan:")
    # print(graph_run['DIY_Final_Plan'])

    # # Ask if the plan is to the user's liking
    # feedback = input("Is this plan to your liking? (yes/no): ").strip().lower()
    #
    # # If the user doesn't like the plan, refine it
    # while feedback != 'yes':
    #     # Get feedback from the user to improve the plan
    #     refinement = input("What would you like to change or improve in the plan? Please be specific: ")
    #
    #     # Update the agent's state with the user's feedback
    #     diystate.human_feedback_string = refinement
    #
    #     # Re-run the graph with the updated feedback
    #     graph_run = graph.invoke(diystate, thread)
    #
    #     # Output the refined DIY plan
    #     print("Refined DIY Plan:")
    #     print(graph_run['DIY_Final_Plan'])
    #
    #     # Ask again if the plan is now to the user's liking
    #     feedback = input("Is this refined plan to your liking? (yes/no): ").strip().lower()


if __name__ == "__main__":
    main()
