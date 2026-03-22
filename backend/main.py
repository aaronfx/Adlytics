"""
ADLYTICS Main Application v4.1 - PRODUCTION READY
Single Web Service deployment with SPA support
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import traceback
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create app instance
app = FastAPI(
    title="ADLYTICS",
    description="AI Ad Pre-Validation SaaS v4.1",
    version="4.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_detail = str(exc)
    traceback_str = traceback.format_exc()
    logger.error(f"Global error: {error_detail}")
    logger.error(f"Traceback: {traceback_str}")

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal Server Error",
            "detail": error_detail,
            "traceback": traceback_str
        }
    )

# SPA Static Files Handler
class SPAStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except HTTPException as ex:
            if ex.status_code == 404:
                return await super().get_response("index.html", scope)
            raise ex

# Import and register API routes BEFORE static files
try:
    from backend.routes.analyze import router as analyze_router
    app.include_router(analyze_router, prefix="/api", tags=["analysis"])
    logger.info("✅ analyze_router loaded successfully")
except Exception as e:
    logger.error(f"❌ Failed to load analyze_router: {e}")
    logger.error(traceback.format_exc())

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "4.1.0",
        "env": {
            "OPENROUTER_API_KEY_SET": bool(os.getenv("OPENROUTER_API_KEY")),
            "PORT": os.getenv("PORT", "8000")
        }
    }

# Mount static files LAST
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/", SPAStaticFiles(directory=frontend_path, html=True), name="static")
    logger.info(f"✅ Static files mounted from {frontend_path}")
else:
    logger.warning(f"⚠️ Frontend path not found: {frontend_path}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
