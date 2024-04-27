from pydantic import BaseModel


class UploadFileRequest(BaseModel):
    user: str


class UploadFileResponse(BaseModel):
    id: str
    name: str
    size: int
    extension: str
    mime_type: str
    created_by: str  # created by user
    created_at: int  # unix timestamp seconds
