FROM python:3.11-slim

WORKDIR /app

# System deps for the Unstructured PDF pipeline: poppler for page rendering,
# tesseract for OCR fallback, libmagic for filetype detection, libgl1 +
# libglib2.0-0 because opencv-python (pulled in by unstructured-inference)
# dynamically links against libGL/libgthread even though we never touch a
# display — this only breaks at import time, so `docker build` succeeds and
# it's only caught when the container actually runs.
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    tesseract-ocr \
    libmagic1 \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# unstructured-inference depends on torch, and plain `pip install torch`
# pulls the CUDA build by default — several GB of NVIDIA libraries we'll
# never use since this runs CPU-only. Installing the CPU wheel first means
# the requirements.txt install below finds it already satisfied and never
# reaches for the CUDA one.
RUN pip install --no-cache-dir torch==2.13.0+cpu torchvision==0.28.0+cpu \
    --index-url https://download.pytorch.org/whl/cpu

# Install deps first so this layer is cached unless requirements.txt changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
