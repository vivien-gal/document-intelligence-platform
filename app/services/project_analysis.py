import re
import unicodedata
from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Document, DocumentChunk
from app.services.search import search_chunks

NOT_FOUND = "Not found"

ANALYSIS_SEARCH_QUERIES = (
    "projekt összefoglaló projekt neve cél",
    "határidő szerződés lejárata dátum",
    "költségkeret havi díj költség budget",
    "kockázatok risk",
    "nyitott feladatok feladatok todo",
    "projektvezető kapcsolattartó felelős stakeholder",
)

DATE_FIELD_PATTERNS = (
    "hatarido",
    "hatarideje",
    "szerzodes lejarat",
    "szerzodes lejarata",
    "deadline",
    "due date",
    "datum",
)

BUDGET_FIELD_PATTERNS = (
    "koltsegkeret",
    "koltseg",
    "havi dij",
    "budget",
    "dij",
)

STAKEHOLDER_FIELD_PATTERNS = (
    "projektvezeto",
    "kapcsolattarto",
    "felelos",
    "contact",
    "project manager",
)

SUMMARY_FIELD_PATTERNS = (
    "projekt neve",
    "projekt celja",
    "osszefoglalo",
    "summary",
    "leiras",
)

RISK_HEADING_PATTERNS = ("kockazat", "risk")
TASK_HEADING_PATTERNS = ("nyitott feladat", "feladat", "open task", "todo")


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.lower())
    folded = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return " ".join(re.findall(r"[a-z0-9]+", folded))


def _matches_any(normalized: str, patterns: Iterable[str]) -> bool:
    return any(pattern in normalized for pattern in patterns)


def _unique_keep_order(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        key = item.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(item.strip())
    return result


def _collect_corpus(db: Session) -> tuple[list[str], list[str]]:
    """Return (text_blocks, source_filenames) from DB + semantic search."""
    documents = db.scalars(select(Document).order_by(Document.id)).all()
    filenames = [doc.filename for doc in documents]

    chunk_by_id: dict[int, str] = {}
    chunks = db.scalars(
        select(DocumentChunk).options(joinedload(DocumentChunk.document))
    ).all()
    for chunk in chunks:
        chunk_by_id[chunk.id] = chunk.content

    for query in ANALYSIS_SEARCH_QUERIES:
        for hit in search_chunks(db, query, limit=8):
            chunk_by_id[hit.chunk_id] = hit.content

    return list(chunk_by_id.values()), filenames


def _extract_colon_fields(text: str, field_patterns: tuple[str, ...]) -> list[str]:
    found: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if ":" not in line:
            continue
        left, right = line.split(":", 1)
        if not right.strip():
            continue
        if _matches_any(_normalize(left), field_patterns):
            found.append(f"{left.strip()}: {right.strip()}")
    return found


def _extract_list_under_headings(text: str, heading_patterns: tuple[str, ...]) -> list[str]:
    lines = [line.rstrip() for line in text.splitlines()]
    items: list[str] = []

    for index, raw in enumerate(lines):
        line = raw.strip()
        if ":" not in line:
            continue
        heading, inline = line.split(":", 1)
        heading_norm = _normalize(heading)
        if not _matches_any(heading_norm, heading_patterns):
            continue

        inline_value = inline.strip()
        if inline_value:
            items.append(inline_value)

        for next_line in lines[index + 1 :]:
            value = next_line.strip()
            if not value:
                if items:
                    break
                continue
            if ":" in value and not value.startswith(("-", "*", "•")):
                break
            bullet = re.sub(r"^[-*•]\s*", "", value).strip()
            if bullet:
                items.append(bullet)

    return items


def _build_project_summary(blocks: list[str]) -> str:
    parts: list[str] = []
    for block in blocks:
        for line in _extract_colon_fields(block, SUMMARY_FIELD_PATTERNS):
            parts.append(line)
        if parts:
            break

    if not parts:
        for block in blocks:
            sentences = [
                s.strip()
                for s in re.split(r"(?<=[.!?])\s+", block.replace("\n", " "))
                if s.strip()
            ]
            if sentences:
                parts.append(sentences[0][:280])
                break

    merged = " ".join(_unique_keep_order(parts))
    return merged if merged else NOT_FOUND


def generate_project_analysis(db: Session) -> dict[str, object]:
    blocks, source_documents = _collect_corpus(db)
    corpus = "\n\n".join(blocks)

    key_dates = _unique_keep_order(
        field
        for block in blocks
        for field in _extract_colon_fields(block, DATE_FIELD_PATTERNS)
    )

    budget_information = _unique_keep_order(
        field
        for block in blocks
        for field in _extract_colon_fields(block, BUDGET_FIELD_PATTERNS)
    )

    risks = _unique_keep_order(
        item
        for block in blocks
        for item in _extract_list_under_headings(block, RISK_HEADING_PATTERNS)
    )

    open_tasks = _unique_keep_order(
        item
        for block in blocks
        for item in _extract_list_under_headings(block, TASK_HEADING_PATTERNS)
    )

    stakeholders = _unique_keep_order(
        field
        for block in blocks
        for field in _extract_colon_fields(block, STAKEHOLDER_FIELD_PATTERNS)
    )

    # Extra pass on full corpus for fields split across chunk boundaries.
    if not key_dates:
        key_dates = _extract_colon_fields(corpus, DATE_FIELD_PATTERNS)
    if not budget_information:
        budget_information = _extract_colon_fields(corpus, BUDGET_FIELD_PATTERNS)
    if not stakeholders:
        stakeholders = _extract_colon_fields(corpus, STAKEHOLDER_FIELD_PATTERNS)
    if not risks:
        risks = _extract_list_under_headings(corpus, RISK_HEADING_PATTERNS)
    if not open_tasks:
        open_tasks = _extract_list_under_headings(corpus, TASK_HEADING_PATTERNS)

    return {
        "project_summary": _build_project_summary(blocks),
        "key_dates": key_dates,
        "budget_information": budget_information,
        "risks": risks,
        "open_tasks": open_tasks,
        "stakeholders": stakeholders,
        "source_documents": source_documents,
    }
