try:
    from enum import StrEnum
except ImportError:
    from strenum import StrEnum
from typing import Union, Optional, List

from pydantic import BaseModel, ConfigDict, field_validator

from dify_client import utils
from dify_client.models.base import Metadata, ErrorResponse
from dify_client.models.workflow import WorkflowStartedData, WorkflowFinishedData, NodeStartedData, NodeFinishedData

STREAM_EVENT_KEY = "event"


class StreamEvent(StrEnum):
    MESSAGE = "message"
    AGENT_MESSAGE = "agent_message"
    AGENT_THOUGHT = "agent_thought"
    MESSAGE_FILE = "message_file"  # need to show file
    WORKFLOW_STARTED = "workflow_started"
    NODE_STARTED = "node_started"
    NODE_FINISHED = "node_finished"
    WORKFLOW_FINISHED = "workflow_finished"
    MESSAGE_END = "message_end"
    MESSAGE_REPLACE = "message_replace"
    ERROR = "error"
    PING = "ping"

    @classmethod
    def new(cls, event: Union["StreamEvent", str]) -> "StreamEvent":
        if isinstance(event, cls):
            return event
        return utils.str_to_enum(cls, event)


class StreamResponse(BaseModel):
    model_config = ConfigDict(extra='allow')

    event: StreamEvent
    task_id: Optional[str] = ""

    @field_validator("event", mode="before")
    def transform_stream_event(cls, event: Union[StreamEvent, str]) -> StreamEvent:
        return StreamEvent.new(event)


class PingResponse(StreamResponse):
    pass


class ErrorStreamResponse(StreamResponse, ErrorResponse):
    message_id: Optional[str] = ""


class MessageStreamResponse(StreamResponse):
    message_id: str
    conversation_id: Optional[str] = ""
    answer: str
    created_at: int  # unix timestamp seconds


class MessageEndStreamResponse(StreamResponse):
    message_id: str
    conversation_id: Optional[str] = ""
    created_at: int  # unix timestamp seconds
    metadata: Optional[Metadata]


class MessageReplaceStreamResponse(MessageStreamResponse):
    pass


class AgentMessageStreamResponse(MessageStreamResponse):
    pass


class AgentThoughtStreamResponse(StreamResponse):
    id: str  # agent thought id
    message_id: str
    conversation_id: str
    position: int  # thought position, start from 1
    thought: str
    observation: str
    tool: str
    tool_input: str
    message_files: List[str] = []
    created_at: int  # unix timestamp seconds


class MessageFileStreamResponse(StreamResponse):
    id: str  # file id
    conversation_id: str
    type: str  # only image
    belongs_to: str  # assistant
    url: str


class WorkflowsStreamResponse(StreamResponse):
    workflow_run_id: str
    data: Optional[Union[
        WorkflowStartedData,
        WorkflowFinishedData,
        NodeStartedData,
        NodeFinishedData]
    ]


class ChatWorkflowsStreamResponse(WorkflowsStreamResponse):
    message_id: str
    conversation_id: str
    created_at: int


_COMPLETION_EVENT_TO_STREAM_RESP_MAPPING = {
    StreamEvent.PING: PingResponse,
    StreamEvent.MESSAGE: MessageStreamResponse,
    StreamEvent.MESSAGE_END: MessageEndStreamResponse,
    StreamEvent.MESSAGE_REPLACE: MessageReplaceStreamResponse,
}

CompletionStreamResponse = Union[
    PingResponse,
    MessageStreamResponse,
    MessageEndStreamResponse,
    MessageReplaceStreamResponse,
]


def build_completion_stream_response(data: dict) -> CompletionStreamResponse:
    event = StreamEvent.new(data.get(STREAM_EVENT_KEY))
    return _COMPLETION_EVENT_TO_STREAM_RESP_MAPPING.get(event, StreamResponse)(**data)


_CHAT_EVENT_TO_STREAM_RESP_MAPPING = {
    StreamEvent.PING: PingResponse,
    # chat
    StreamEvent.MESSAGE: MessageStreamResponse,
    StreamEvent.MESSAGE_END: MessageEndStreamResponse,
    StreamEvent.MESSAGE_REPLACE: MessageReplaceStreamResponse,
    StreamEvent.MESSAGE_FILE: MessageFileStreamResponse,
    # agent
    StreamEvent.AGENT_MESSAGE: AgentMessageStreamResponse,
    StreamEvent.AGENT_THOUGHT: AgentThoughtStreamResponse,
    # workflow
    StreamEvent.WORKFLOW_STARTED: WorkflowsStreamResponse,
    StreamEvent.NODE_STARTED: WorkflowsStreamResponse,
    StreamEvent.NODE_FINISHED: WorkflowsStreamResponse,
    StreamEvent.WORKFLOW_FINISHED: WorkflowsStreamResponse,
}

ChatStreamResponse = Union[
    PingResponse,
    MessageStreamResponse,
    MessageEndStreamResponse,
    MessageReplaceStreamResponse,
    MessageFileStreamResponse,
    AgentMessageStreamResponse,
    AgentThoughtStreamResponse,
    WorkflowsStreamResponse,
]


def build_chat_stream_response(data: dict) -> ChatStreamResponse:
    event = StreamEvent.new(data.get(STREAM_EVENT_KEY))
    return _CHAT_EVENT_TO_STREAM_RESP_MAPPING.get(event, StreamResponse)(**data)


_WORKFLOW_EVENT_TO_STREAM_RESP_MAPPING = {
    StreamEvent.PING: PingResponse,
    # workflow
    StreamEvent.WORKFLOW_STARTED: WorkflowsStreamResponse,
    StreamEvent.NODE_STARTED: WorkflowsStreamResponse,
    StreamEvent.NODE_FINISHED: WorkflowsStreamResponse,
    StreamEvent.WORKFLOW_FINISHED: WorkflowsStreamResponse,
}

WorkflowsRunStreamResponse = Union[
    PingResponse,
    WorkflowsStreamResponse,
]


def build_workflows_stream_response(data: dict) -> WorkflowsRunStreamResponse:
    event = StreamEvent.new(data.get(STREAM_EVENT_KEY))
    return _WORKFLOW_EVENT_TO_STREAM_RESP_MAPPING.get(event, StreamResponse)(**data)
