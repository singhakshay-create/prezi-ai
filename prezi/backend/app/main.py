import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from app.api.endpoints import router
from app.database import init_db
from app.config import settings
from app.ws.manager import set_main_loop, connect, disconnect

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("prezi")

# Initialize database
init_db()


class RequestLogMiddleware(BaseHTTPMiddleware):
    """Log every request with method, path, and response status."""

    async def dispatch(self, request: Request, call_next):
        logger.info(f"--> {request.method} {request.url.path} (from {request.client.host})")
        response = await call_next(request)
        logger.info(f"<-- {request.method} {request.url.path} => {response.status_code}")
        if response.status_code >= 400:
            logger.warning(f"    ERROR: {request.method} {request.url.path} returned {response.status_code}")
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Capture the main event loop for WebSocket manager on startup."""
    set_main_loop(asyncio.get_event_loop())
    yield


# Create FastAPI app
app = FastAPI(
    title="Prezi AI API",
    description="AI-powered consulting presentation generator",
    version="1.0.0",
    lifespan=lifespan,
)

# Add request logging (must be added before CORS so it wraps everything)
app.add_middleware(RequestLogMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Prezi AI",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "database": "connected"
    }


@app.websocket("/ws/progress/{job_id}")
async def websocket_progress(websocket: WebSocket, job_id: str):
    """WebSocket endpoint for real-time job progress updates."""
    await websocket.accept()
    connect(job_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        disconnect(job_id, websocket)
