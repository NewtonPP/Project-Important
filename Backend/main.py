import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.endpoints import router
from api.dependencies import global_exception_handler
from models.database import init_db

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("Starting ClarityVoice backend...")
    init_db()
    logger.info("Database initialized")
    yield
    logger.info("Shutting down ClarityVoice backend...")


app = FastAPI(
    title="ClarityVoice API",
    description="Cognitive offloading tool: Transform voice brain dumps into actionable tasks",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(Exception, global_exception_handler)

app.include_router(router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "clarityvoice-backend",
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "ClarityVoice API",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
