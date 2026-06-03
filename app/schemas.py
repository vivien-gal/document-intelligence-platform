from datetime import datetime

from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    id: int
    filename: str
    created_at: datetime
    chunk_count: int

    model_config = {"from_attributes": True}


class ChunkResponse(BaseModel):
    id: int
    document_id: int
    chunk_index: int
    content: str

    model_config = {"from_attributes": True}


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(default=5, ge=1, le=50)


class SearchResult(BaseModel):
    chunk_id: int
    document_id: int
    filename: str
    chunk_index: int
    content: str
    score: float


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    limit: int = Field(default=5, ge=1, le=50)


class ChatResponse(BaseModel):
    answer: str
    sources: list[SearchResult]


class ProjectAnalysisResponse(BaseModel):
    project_summary: str
    key_dates: list[str]
    budget_information: list[str]
    risks: list[str]
    open_tasks: list[str]
    stakeholders: list[str]
    source_documents: list[str]
