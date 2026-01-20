"""FastAPI application entry point."""
import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from core.config import settings
from middleware.orchestrator import Orchestrator
from routers import health, sss2, snapshots, catalog, connection


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global orchestrator instance
_orchestrator: Orchestrator | None = None


def get_orchestrator_instance() -> Orchestrator:
    """Get global orchestrator instance."""
    if _orchestrator is None:
        raise RuntimeError("Orchestrator not initialized")
    return _orchestrator


# ---------- Lifespan handler ----------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    global _orchestrator
    
    # --- STARTUP ---
    logger.info("Starting SSS2 Control Backend...")
    print("=" * 50)
    print("SSS2 Control Backend Starting...")
    print("=" * 50)
    
    try:
        # Initialize orchestrator
        _orchestrator = Orchestrator()
        await _orchestrator.initialize()
        
        logger.info("SSS2 Control Backend started")
    except Exception as e:
        logger.error(f"Failed to start backend: {e}", exc_info=True)
        print(f"ERROR: Failed to start backend: {e}")
        raise
    
    yield
    
    # --- SHUTDOWN ---
    logger.info("Shutting down SSS2 Control Backend...")
    
    if _orchestrator:
        await _orchestrator.shutdown()
    
    logger.info("SSS2 Control Backend shut down")


# ---------- FastAPI Application ----------
app = FastAPI(
    title="SSS2 Control Backend",
    description="Smart Sensor Simulation 2 Control System",
    version=settings.VERSION,
    lifespan=lifespan
)

# Add request logging middleware
@app.middleware("http")
async def log_requests(request, call_next):
    """Log all incoming requests."""
    start_time = time.time()
    client_host = request.client.host if request.client else 'unknown'
    logger.info(f"→ {request.method} {request.url.path} from {client_host}")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(f"← {request.method} {request.url.path} {response.status_code} ({process_time:.3f}s)")
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"✗ {request.method} {request.url.path} ERROR after {process_time:.3f}s: {e}", exc_info=True)
        raise

# ---------- API Routes ----------
app.include_router(health.router, prefix="/api")
app.include_router(sss2.router, prefix="/api")
app.include_router(snapshots.router, prefix="/api")
app.include_router(catalog.router, prefix="/api")
app.include_router(connection.router, prefix="/api")


# ---------- Static File Serving ----------
# Mount static UI files if directory exists
static_ui_path = Path(__file__).parent / "static" / "ui"
if static_ui_path.exists():
  assets_path = static_ui_path / "assets"
  if assets_path.exists() and assets_path.is_dir():
    app.mount("/static", StaticFiles(directory=str(assets_path)), name="static")
    
    # Serve index.html for all non-API routes
    @app.get("/{full_path:path}")
    async def serve_ui(full_path: str):
        """Serve UI files."""
        # Don't serve API routes
        if full_path.startswith("api"):
            return None
        
        # Try to serve the file, fallback to index.html for SPA routing
        file_path = static_ui_path / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        
        # Default to index.html for SPA
        index_path = static_ui_path / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        
        return {"error": "UI not found. Run 'npm run build' in ui/ directory."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
