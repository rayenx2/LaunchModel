import json
import logging
import os
import threading
import time
from typing import Any, Dict, List

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from pydantic import BaseModel, Field, field_validator
from starlette.responses import Response

MODEL_PATH = os.getenv("MODEL_PATH", "model/artifacts/model.pkl")
ENCODER_PATH = os.getenv("ENCODER_PATH", "model/artifacts/encoder.pkl")
METRICS_PATH = os.getenv("METRICS_PATH", "model/artifacts/metrics.json")
REQUEST_LOG = os.getenv("REQUEST_LOG", "ops/data/live_requests.jsonl")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

REQUEST_COUNT = Counter("inference_requests_total", "Total inference requests")
REQUEST_ERRORS = Counter("inference_errors_total", "Total inference errors")
REQUEST_LATENCY = Histogram("inference_latency_seconds", "Inference latency in seconds")

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("launchmodel")

app = FastAPI(title="LaunchModel API", version="0.3.0")

REQUIRED_FEATURES = [
    "age", "workclass", "fnlwgt", "education", "education_num",
    "marital_status", "occupation", "relationship", "race", "sex",
    "capital_gain", "capital_loss", "hours_per_week", "native_country",
]


class Features(BaseModel):
    features: Dict[str, Any] = Field(..., description="Adult-census feature dict")

    @field_validator("features")
    @classmethod
    def validate_features(cls, value: Dict[str, Any]) -> Dict[str, Any]:
        if not value:
            raise ValueError("features dict must not be empty")
        missing = [f for f in REQUIRED_FEATURES if f not in value]
        if missing:
            raise ValueError(f"missing required features: {missing}")
        return value


def load_artifacts():
    model = joblib.load(MODEL_PATH)
    encoder = joblib.load(ENCODER_PATH)
    return model, encoder


def load_training_metrics() -> Dict[str, Any]:
    if os.path.exists(METRICS_PATH):
        with open(METRICS_PATH) as f:
            return json.load(f)
    return {}


model, encoder = load_artifacts()
TRAINING_METRICS = load_training_metrics()
MODEL_LOADED_AT = time.time()


@app.middleware("http")
async def add_logging_and_metrics(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    REQUEST_LATENCY.observe(duration)
    logger.info(
        "%s %s -> %s (%.4fs)",
        request.method, request.url.path, response.status_code, duration,
    )
    return response


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/model/info")
def model_info():
    """Model metadata and training metrics for the MLOps dashboard."""
    return {
        "model_type": type(model).__name__,
        "training_metrics": TRAINING_METRICS,
        "model_path": MODEL_PATH,
        "encoder_path": ENCODER_PATH,
        "loaded_at": MODEL_LOADED_AT,
        "uptime_seconds": round(time.time() - MODEL_LOADED_AT, 2),
        "required_features": REQUIRED_FEATURES,
    }


@app.get("/predictions/recent")
def predictions_recent(limit: int = 20) -> Dict[str, Any]:
    """Return the most recent live predictions (in-memory tail of the request log)."""
    limit = max(1, min(limit, 200))
    rows: List[Dict[str, Any]] = []
    if os.path.exists(REQUEST_LOG):
        with open(REQUEST_LOG) as f:
            for line in f:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    recent = rows[-limit:]
    return {"count": len(recent), "total_logged": len(rows), "predictions": recent}


@app.post("/predict")
def predict(payload: Features):
    REQUEST_COUNT.inc()
    try:
        X = encoder.transform(pd.DataFrame([payload.features]))
        y = model.predict_proba(X)[0, 1]
        rec = {"ts": time.time(), "features": payload.features, "prediction": float(y)}

        def _write():
            try:
                log_dir = os.path.dirname(REQUEST_LOG)
                if log_dir:
                    os.makedirs(log_dir, exist_ok=True)
                with open(REQUEST_LOG, "a") as f:
                    f.write(json.dumps(rec) + "\n")
            except OSError as exc:
                logger.warning("failed to write request log: %s", exc)

        threading.Thread(target=_write, daemon=True).start()
        return {"probability_over_50k": float(y)}
    except Exception as exc:
        REQUEST_ERRORS.inc()
        logger.exception("prediction failed")
        raise HTTPException(status_code=400, detail=f"prediction failed: {exc}")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def root():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "LaunchModel API. See /docs."}
