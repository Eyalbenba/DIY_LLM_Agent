
from __future__ import annotations
from DIYAgent import diyprompts

from dataclasses import dataclass, field, fields,asdict
from typing import Annotated, Any, Literal, Optional, Type, TypeVar
from langchain_core.runnables import RunnableConfig, ensure_config
import uuid


@dataclass(kw_only=True)
class DIYAgentConfiguration:
    """The configuration for the DIY agent."""

    # System prompt for generating responses to the user's DIY-related questions
    diyplan_system_prompt: str = field(
        default=diyprompts.DIYPLAN_SYSTEM_PROMPT,
        metadata={"description": "The diyplan system prompt used for generating responses."},
    )

    # The language model used for generating responses
    response_model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
        default="openai/gpt-3.5-turbo-0125",
        metadata={
            "description": "The language model used for generating responses. Should be in the form: provider/model-name."
        },
    )

    # System prompt for refining and processing user queries
    query_system_prompt: str = field(
        default=diyprompts.QUERY_SYSTEM_PROMPT,
        metadata={
            "description": "The system prompt used for processing and refining queries."
        },
    )

    # The language model used for refining and processing queries
    query_model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
        default="openai/gpt-3.5-turbo-0125",
        metadata={
            "description": "The language model used for processing and refining queries. Should be in the form: provider/model-name."
        },
    )

    # Additional search prompt for queries specifically related to search operations
    search_system_prompt: str = field(
        default=diyprompts.SEARCH_INSTRUCTIONS_PROPMT,
        metadata={
            "description": "The system prompt used for search-related queries."
        },
    )

    # The language model used for search query processing
    search_query_model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
        default="openai/gpt-3.5-turbo-0125",
        metadata={
            "description": "The language model used for processing search queries. Should be in the form: provider/model-name."
        },
    )

    # New thread_id field for memory checkpointing
    thread_id: str = field(
        default_factory=lambda: str(uuid.uuid4()),  # Auto-generate a unique thread ID if not provided
        metadata={
            "description": "Unique identifier for the current thread to be used with memory checkpointing."
        },
    )

    @classmethod
    def from_runnable_config(
            cls: Type[T], config: Optional[RunnableConfig] = None
    ) -> T:
        """Create an DIYAgentConfiguration instance from a RunnableConfig object.

        Args:
            cls (Type[T]): The class itself.
            config (Optional[RunnableConfig]): The configuration object to use.

        Returns:
            T: An instance of DIYAgentConfiguration with the specified configuration.
        """
        config = ensure_config(config)
        configurable = config.get("configurable") or {}
        _fields = {f.name for f in fields(cls) if f.init}
        return cls(**{k: v for k, v in configurable.items() if k in _fields})

    def to_dict(self) -> dict:
        """Convert the configuration instance to a dictionary."""
        return asdict(self)

T = TypeVar("T", bound=DIYAgentConfiguration)