import json
import re

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import DocumentChunk
from app.schemas import SearchResult
from app.services.embeddings import cosine_similarity, embed_query

PRIORITY_FIELDS = (
    "projektvezető",
    "projekt neve",
    "határidő",
    "költségkeret",
)


def _tokenize(text: str) -> list[str]:
    return [t for t in re.findall(r"\w+", text.lower(), flags=re.UNICODE) if len(t) > 1]


def _exact_keyword_boost(query: str, content: str) -> float:
    query_lower = query.lower().strip()
    content_lower = content.lower()
    boost = 0.0

    if query_lower and query_lower in content_lower:
        boost += 0.35

    tokens = _tokenize(query)
    if tokens:
        exact_hits = 0
        for token in tokens:
            # Prefer exact word-level matches over loose semantic-only matches.
            if re.search(rf"\b{re.escape(token)}\b", content_lower):
                exact_hits += 1
        boost += min(0.45, exact_hits * 0.09)

    return boost


def _field_name_boost(query: str, content: str) -> float:
    query_lower = query.lower()
    content_lower = content.lower()
    boost = 0.0

    for field_name in PRIORITY_FIELDS:
        field_tokens = _tokenize(field_name)
        # Only apply field boost when the query is explicitly asking about that field.
        if any(token in query_lower for token in field_tokens) and field_name in content_lower:
            boost += 0.34

    return min(boost, 0.9)


def _rerank_score(semantic_score: float, query: str, content: str) -> float:
    return (
        semantic_score * 0.7
        + _exact_keyword_boost(query, content)
        + _field_name_boost(query, content)
    )


def search_chunks(db: Session, query: str, limit: int) -> list[SearchResult]:
    query_embedding = embed_query(query)

    chunks = db.scalars(
        select(DocumentChunk).options(joinedload(DocumentChunk.document))
    ).all()

    semantic_ranked: list[SearchResult] = []
    for chunk in chunks:
        chunk_embedding = json.loads(chunk.embedding)
        score = cosine_similarity(query_embedding, chunk_embedding)
        semantic_ranked.append(
            SearchResult(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                filename=chunk.document.filename,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                score=score,
            )
        )

    # Stage 1: semantic retrieval.
    semantic_ranked.sort(key=lambda item: item.score, reverse=True)
    candidates = semantic_ranked[: max(limit * 8, 30)]

    # Stage 2: reranking with lexical and field-specific boosts.
    reranked: list[SearchResult] = []
    for item in candidates:
        final_score = _rerank_score(item.score, query, item.content)
        reranked.append(
            SearchResult(
                chunk_id=item.chunk_id,
                document_id=item.document_id,
                filename=item.filename,
                chunk_index=item.chunk_index,
                content=item.content,
                score=final_score,
            )
        )

    # Highest ranked chunk is always first.
    reranked.sort(key=lambda item: item.score, reverse=True)
    return reranked[:limit]
