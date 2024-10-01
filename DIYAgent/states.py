
from dataclasses import dataclass, field
from typing import Annotated, Any, Literal, Optional, Sequence, Union
from langchain_core.pydantic_v1 import BaseModel,Field
from langchain_core.documents import Document
from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages

@dataclass(kw_only=True)
class InputState:
    """Represents the input state for the agent.

    This class defines the structure of the input state, which includes
    the messages exchanged between the user and the agent. It serves as
    a restricted version of the full State, providing a narrower interface
    to the outside world compared to what is maintained internally.
    """

    messages: Annotated[Sequence[AnyMessage], add_messages]


# This is the primary state of your agent, where you can store any information


def add_queries(existing: Sequence[str], new: Sequence[str]) -> Sequence[str]:
    """Combine existing queries with new queries.

    Args:
        existing (Sequence[str]): The current list of queries in the state.
        new (Sequence[str]): The new queries to be added.

    Returns:
        Sequence[str]: A new list containing all queries from both input sequences.
    """
    return list(existing) + list(new)


@dataclass(kw_only=True)
class DIYAgentState(InputState):
    """The state of your graph / agent."""
    user_query :str

    queries: Annotated[list[str], add_queries] = field(default_factory=list)
    """A list of search queries that the agent has generated."""

    retrieved_docs: list[Document] = field(default_factory=list)
    """Populated by the retriever. This is a list of documents that the agent can reference."""

class SearchQuery(BaseModel):
    search_query: str = Field(None, description="Search query for retrieval.")


class DIYPlan(BaseModel):
    plan: str = Field(None, description="DIY plan generated by the agent.")