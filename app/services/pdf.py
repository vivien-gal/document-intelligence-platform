from io import BytesIO

from pypdf import PdfReader

from app.config import settings


def extract_text_from_pdf(data: bytes) -> str:
    reader = PdfReader(BytesIO(data))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages).strip()


def chunk_text(text: str) -> list[str]:
    if not text:
        return []

    size = settings.chunk_size
    overlap = settings.chunk_overlap
    if overlap >= size:
        overlap = max(0, size // 4)

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = end - overlap

    return chunks
