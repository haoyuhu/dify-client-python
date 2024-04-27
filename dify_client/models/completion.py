from typing import Optional, List

from pydantic import BaseModel

from dify_client.models.base import CompletionInputs, ResponseMode, File, Metadata, Mode


class CompletionRequest(BaseModel):
    inputs: CompletionInputs
    response_mode: ResponseMode
    user: str
    conversation_id: Optional[str] = ""
    files: List[File] = []


class CompletionResponse(BaseModel):
    message_id: str
    conversation_id: Optional[str] = ""
    mode: Mode
    answer: str
    metadata: Metadata
    created_at: int  # unix timestamp seconds
