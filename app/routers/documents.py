import json

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Document, DocumentChunk
from app.schemas import (
    ChunkResponse,
    DocumentResponse,
    SearchRequest,
    SearchResult,
)
from app.services.embeddings import embed_texts
from app.services.pdf import chunk_text, extract_text_from_pdf
from app.services.search import search_chunks

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> DocumentResponse:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")

    pdf_text = extract_text_from_pdf(data)
    if not pdf_text:
        raise HTTPException(status_code=400, detail="No extractable text in PDF")

    chunks = chunk_text(pdf_text)
    if not chunks:
        raise HTTPException(status_code=400, detail="No text chunks produced")

    embeddings = embed_texts(chunks)

    document = Document(filename=file.filename)
    db.add(document)
    db.flush()

    for index, (content, embedding) in enumerate(zip(chunks, embeddings, strict=True)):
        db.add(
            DocumentChunk(
                document_id=document.id,
                chunk_index=index,
                content=content,
                embedding=json.dumps(embedding),
            )
        )

    db.commit()
    db.refresh(document)

    return DocumentResponse(
        id=document.id,
        filename=document.filename,
        created_at=document.created_at,
        chunk_count=len(chunks),
    )


@router.get("", response_model=list[DocumentResponse])
def list_documents(db: Session = Depends(get_db)) -> list[DocumentResponse]:
    documents = db.scalars(select(Document).order_by(Document.id.desc())).all()
    return [
        DocumentResponse(
            id=doc.id,
            filename=doc.filename,
            created_at=doc.created_at,
            chunk_count=len(doc.chunks),
        )
        for doc in documents
    ]


@router.get("/{document_id}/chunks", response_model=list[ChunkResponse])
def list_chunks(document_id: int, db: Session = Depends(get_db)) -> list[ChunkResponse]:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    chunks = sorted(document.chunks, key=lambda c: c.chunk_index)
    return [
        ChunkResponse(
            id=chunk.id,
            document_id=chunk.document_id,
            chunk_index=chunk.chunk_index,
            content=chunk.content,
        )
        for chunk in chunks
    ]


@router.delete("/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))
    db.delete(document)
    db.commit()

    return {
        "message": "Document deleted successfully",
        "document_id": document_id,
    }


@router.post("/search", response_model=list[SearchResult])
def search_documents(
    body: SearchRequest,
    db: Session = Depends(get_db),
) -> list[SearchResult]:
    return search_chunks(db, body.query, body.limit)
