from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ChatRequest, ChatResponse
from app.services.chat import build_answer
from app.services.search import search_chunks

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    sources = search_chunks(db, body.message, body.limit)
    answer = build_answer(body.message, sources)
    return ChatResponse(answer=answer, sources=sources)
