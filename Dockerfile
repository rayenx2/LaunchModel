# syntax=docker/dockerfile:1
FROM python:3.11-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
RUN useradd -m appuser
WORKDIR /app

FROM base AS builder
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip wheel --wheel-dir /wheels -r requirements.txt

FROM base AS runtime
COPY --from=builder /wheels /wheels
RUN pip install --no-index --find-links=/wheels /wheels/* && rm -rf /wheels
COPY . .
RUN chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
ENV MODEL_PATH=model/artifacts/model.pkl ENCODER_PATH=model/artifacts/encoder.pkl REQUEST_LOG=ops/data/live_requests.jsonl
CMD ["gunicorn","-k","uvicorn.workers.UvicornWorker","-b","0.0.0.0:8000","app.main:app","--workers","2"]
