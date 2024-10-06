from DIYAgent.DIYAgentGraph import *
from DIYAgent.states import *
from DIYAgent.utils import *
from DIYAgent.config import *

if __name__ == '__main__':
    user_query = get_initial_user_query()
    diystate = DIYAgentState(user_query=user_query)
    diy_graph = build_diy_graph()
    diy_config = DIYAgentConfiguration()
    diy_graph.invoke(state=diystate, config=diy_config)