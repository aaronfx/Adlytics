"""
ADLYTICS Main Application v4.1
Single Web Service deployment on Render
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
import os

# Create app instance FIRST (must be at module level for uvicorn)
app = FastAPI(
    title="ADLYTICS",
    description="AI Ad Pre-Validation SaaS",
    version="4.1.0"
)

# SPA Static Files Handler (for client-side routing)
class SPAStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except HTTPException as ex:
            if ex.status_code == 404:
                # Return index.html for any 404 (client-side routing)
                return await super().get_response("index.html", scope)
            raise ex

# Import and register API routes FIRST (before static files)
from backend.routes.analyze import router as analyze_router
app.include_router(analyze_router, prefix="/api", tags=["analysis"])

# Health check endpoint (before static files)
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "4.1.0"}

# Mount static files LAST (after all API routes)
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/", SPAStaticFiles(directory=frontend_path, html=True), name="static")

# This allows running with: uvicorn backend.main:app
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
