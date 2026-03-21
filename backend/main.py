"""
ADLYTICS - AI Ad Pre-Validation & ROI Simulator
Main FastAPI Application (Single Web Service Deployment)
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from pathlib import Path
import os

from backend.routes.analyze import router as analyze_router

# Determine static files path
static_path = Path(__file__).parent.parent / "frontend"
if not static_path.exists():
    static_path = Path("frontend")

# Custom StaticFiles for SPA support
class SPAStaticFiles(StaticFiles):
    """Custom StaticFiles that serves index.html for 404s (SPA support)"""
    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except (HTTPException, StarletteHTTPException) as ex:
            if ex.status_code == 404:
                # Serve index.html for any 404 (client-side routing)
                return await super().get_response("index.html", scope)
            else:
                raise ex

app = FastAPI(
    title="ADLYTICS API",
    description="AI-powered ad pre-validation and ROI simulation",
    version="1.0.0"
)

# CORS - Allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes FIRST (before static files)
app.include_router(analyze_router, prefix="/api", tags=["analysis"])

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Mount static files LAST with SPA support
if static_path.exists():
    app.mount("/", SPAStaticFiles(directory=str(static_path), html=True), name="spa")
else:
    @app.get("/")
    async def root_no_static():
        return {"message": "ADLYTICS API - Frontend not built", "status": "running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
