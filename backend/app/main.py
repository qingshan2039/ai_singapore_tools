"""FastAPI 应用入口"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import analytics, toto

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Starting TOTO Analyzer API")
    # TODO P0-Week2: 这里启动 APScheduler
    yield
    log.info("Shutting down")


app = FastAPI(
    title="TOTO Analyzer",
    description="Singapore TOTO historical data & analytics. **For entertainment only.**",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(toto.router)
app.include_router(analytics.router)


@app.get("/")
async def root():
    return {
        "name": "TOTO Analyzer API",
        "version": "0.1.0",
        "docs": "/docs",
        "disclaimer": (
            "All statistics provided are for entertainment purposes only. "
            "Lottery draws are mathematically independent events; past results "
            "do not predict future outcomes."
        ),
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
