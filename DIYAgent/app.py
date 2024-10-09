from DIYAgent.DIYAgentGraph import *
from DIYAgent.states import *
from DIYAgent.utils import *
from DIYAgent.config import *

if __name__ == '__main__':
    initial_messages = []
    user_query = get_initial_user_query()
    diystate = DIYAgentState(user_query=user_query,messages=initial_messages)
    diy_config = DIYAgentConfiguration()
    diy_config_dict = diy_config.to_dict()
    diy_graph = build_diy_graph()
    # diy_graph.invoke({'state':diystate},config=diy_config_dict)
    # Step 3: Stream the graph and debug outputs at each step
    print("Running the graph...")

    # Loop through the stream of events from the graph
    for event in diy_graph.stream(input={"state": diystate}, config=diy_config_dict, stream_mode="values"):
        # Step 4: Review the output from the event
        print("Event received:", event)
        if event:
            print(event)