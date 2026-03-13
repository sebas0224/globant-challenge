from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.database import init_db
from app.routers import upload, metrics


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the database tables on startup."""
    init_db()
    yield


app = FastAPI(
    title="Globant Data Engineering Challenge",
    description=(
        "REST API for DB migration with CSV upload, batch inserts, "
        "and analytics endpoints."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(upload.router)
app.include_router(metrics.router)


@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "message": "Globant DE Challenge API is running."}
