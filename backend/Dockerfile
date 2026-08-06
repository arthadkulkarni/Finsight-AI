FROM python:3.11-slim

WORKDIR /app

# System deps for the Unstructured PDF pipeline: poppler for page rendering,
# tesseract for OCR fallback, libmagic for filetype detection.
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    tesseract-ocr \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Install deps first so this layer is cached unless requirements.txt changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
