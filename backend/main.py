"""
ADLYTICS Backend API
Version: 8.0.0

Main FastAPI application with routers for ad analysis, rewriting, and video funnel analysis.
"""

import logging
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="ADLYTICS",
    version="8.0.0",
    description="AI-powered ad analysis, rewriting, and video funnel analysis platform"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers
try:
    from backend.routes.analyze import router as analyze_router
    from backend.routes.rewrite import router as rewrite_router
    from backend.routes.video_funnel import router as video_funnel_router
    from backend.routes.meta_ads import router as meta_router
    from backend.routes.creative_gen import router as creative_router
    logger.info("Successfully imported all routers")
except ImportError as e:
    logger.warning(f"Failed to import routers: {e}")
    analyze_router = None
    rewrite_router = None
    video_funnel_router = None
    meta_router = None
    creative_router = None

# Mount routers
if analyze_router:
    app.include_router(analyze_router, prefix="/api")
if rewrite_router:
    app.include_router(rewrite_router, prefix="/api")
if video_funnel_router:
    app.include_router(video_funnel_router, prefix="/api")
if meta_router:
    app.include_router(meta_router, prefix="/api")
if creative_router:
    app.include_router(creative_router, prefix="/api")

# Health endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "8.0.0",
        "service": "ADLYTICS"
    }

# Test endpoint
@app.get("/api/test")
async def test_endpoint():
    """Test endpoint for API connectivity"""
    return {
        "message": "API is working correctly",
        "version": "8.0.0"
    }

# OPTIONS handler for analyze endpoint
@app.options("/api/analyze")
async def analyze_options():
    """CORS preflight handler for analyze endpoint"""
    return {"status": "ok"}

# Determine static files path
backend_dir = Path(__file__).parent
project_root = backend_dir.parent
frontend_dir = project_root / "frontend"

if frontend_dir.exists():
    logger.info(f"Frontend directory found at: {frontend_dir}")
else:
    logger.warning(f"Frontend directory not found at {frontend_dir}")

# Root endpoint - serve app.html
@app.get("/")
async def root():
    """Serve the main app.html"""
    app_html = frontend_dir / "app.html"
    if app_html.exists():
        return FileResponse(app_html)
    return {"message": "ADLYTICS API v8.0.0"}

# SPA catch-all - serve app.html for any unmatched routes
@app.get("/{full_path:path}")
async def spa_fallback(full_path: str):
    """Catch-all handler for SPA routing - serves app.html"""
    app_html = frontend_dir / "app.html"
    if app_html.exists() and not full_path.startswith("api/"):
        return FileResponse(app_html)
    return {"error": "Not found", "path": full_path}, 404

if __name__ == "__main__":
    logger.info("Starting ADLYTICS Backend API v8.0.0")
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
