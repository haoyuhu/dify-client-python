try:
    from enum import StrEnum
except ImportError:
    from strenum import StrEnum
from http import HTTPStatus
from typing import Optional, List

from pydantic import BaseModel, ConfigDict


class Mode(StrEnum):
    CHAT = "chat"
    COMPLETION = "completion"


class ResponseMode(StrEnum):
    STREAMING = 'streaming'
    BLOCKING = 'blocking'


class FileType(StrEnum):
    IMAGE = "image"


class TransferMethod(StrEnum):
    REMOTE_URL = "remote_url"
    LOCAL_FILE = "local_file"


# Allows the entry of various variable values defined by the App.
# The inputs parameter contains multiple key/value pairs, with each key corresponding to a specific variable and
# each value being the specific value for that variable.
# The text generation application requires at least one key/value pair to be inputted.
class CompletionInputs(BaseModel):
    model_config = ConfigDict(extra='allow')
    # Required The input text, the content to be processed.
    query: str


class File(BaseModel):
    type: FileType
    transfer_method: TransferMethod
    url: Optional[str]
    # Uploaded file ID, which must be obtained by uploading through the File Upload API in advance
    # (when the transfer method is local_file)
    upload_file_id: Optional[str]


class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

    prompt_unit_price: str
    prompt_price_unit: str
    prompt_price: str
    completion_unit_price: str
    completion_price_unit: str
    completion_price: str
    total_price: str
    currency: str

    latency: float


class RetrieverResource(BaseModel):
    position: int
    dataset_id: str
    dataset_name: str
    document_id: str
    document_name: str
    segment_id: str
    score: float
    content: str


class Metadata(BaseModel):
    usage: Usage
    retriever_resources: List[RetrieverResource] = []


class StopRequest(BaseModel):
    user: str


class StopResponse(BaseModel):
    result: str  # success


class ErrorResponse(BaseModel):
    status: int = HTTPStatus.INTERNAL_SERVER_ERROR  # HTTP status code
    code: str = ""
    message: str = ""
