from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.db.mongo import DEFAULT_MONGODB_COLLECTION, MongoTransactionRepository
from app.models.schemas import (
    BatchPredictionRequest,
    BatchPredictionResponse,
)
from app.core.logging import setup_logging
from app.services.batch import score_batch_documents
from app.services.ml import MODEL_VERSION, get_model
import os

logger = setup_logging()

app = FastAPI(
    title="Broadband Fraud Batch API",
    description="MongoDB-backed batch fraud scoring for broadband accounts",
    version="1.0.0",
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.on_event("startup")
def load_model_on_startup():
    # Force the XGBoost model to load once at startup instead of on the
    # first request, so the first real request isn't slow.
    get_model()
    logger.info("XGBoost model loaded, version=%s", MODEL_VERSION)


@app.get("/")
def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict", response_model=BatchPredictionResponse)
def predict_batch(request: BatchPredictionRequest):
    repository = MongoTransactionRepository()
    collection_name = request.collection_name or DEFAULT_MONGODB_COLLECTION

    try:
        documents = repository.fetch_transactions(
            collection_name=request.collection_name,
            customer_id=request.customer_id,
            skip=request.skip,
            limit=request.limit,
        )
        predictions, summary = score_batch_documents(documents)
    except Exception as e:
        logger.exception("Batch prediction failed for collection=%s", collection_name)
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {e}")

    return BatchPredictionResponse(
        collection_name=collection_name,
        matched_count=len(predictions),
        predictions=predictions,
        summary=summary,
    )
