FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DATA_DIR=/app/data \
    DATABASE_URL=sqlite:////app/data/app.db \
    HF_HOME=/app/.cache/huggingface \
    # Prevent accidental CUDA wheel selection
    PIP_EXTRA_INDEX_URL=

RUN mkdir -p /app/data /app/.cache/huggingface

COPY requirements.txt requirements-ml.txt ./

# Install CPU-only PyTorch first (~200MB vs ~2GB+ CUDA builds)
RUN pip install --no-cache-dir \
    "torch==2.5.1" \
    --index-url https://download.pytorch.org/whl/cpu

# App + sentence-transformers (torch already satisfied — pip won't pull CUDA)
RUN pip install --no-cache-dir \
    -r requirements.txt \
    -r requirements-ml.txt

# Pre-download embedding model during build
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

COPY app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
