"""
ADLYTICS v5.9 - REAL SCORING ONLY
No fake scores. Debug mode. Content-specific analysis guaranteed.
"""

from fastapi import APIRouter, Form, UploadFile, File, HTTPException
from typing import Optional, List, Dict, Any
import os
import traceback
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Import v5.9 engine
try:
    from backend.services.ai_engine_v59 import get_ai_engine
    ai_engine = get_ai_engine()
    logger.info("✅ AI Engine v5.9 loaded")
except Exception as e:
    logger.error(f"❌ Failed to load v5.9 engine: {e}")
    ai_engine = None

@router.post("/analyze")
async def analyze_endpoint(
    ad_copy: Optional[str] = Form(None),
    video_script: Optional[str] = Form(None),
    platform: str = Form(...),
    industry: str = Form(...),
    audience_country: str = Form("nigeria"),
    audience_age: str = Form("25-34"),
    debug: bool = Form(False),  # NEW: Debug mode
    image: Optional[UploadFile] = File(None),
    video: Optional[UploadFile] = File(None)
):
    """
    v5.9: Real content-specific analysis. 
    If scores are generic, returns error instead of fake data.
    """

    try:
        logger.info(f"📥 V5.9 Analysis Request (debug={debug})")

        if ai_engine is None:
            raise HTTPException(status_code=503, detail="AI Engine not available")

        # Determine content
        content = ""
        if video_script:
            content = video_script
            content_type = "video_script"
        elif ad_copy:
            content = ad_copy
            content_type = "ad_copy"
        else:
            raise HTTPException(status_code=400, detail="No content provided")

        # Build request
        request_data = {
            "ad_copy": ad_copy or "",
            "video_script": video_script or "",
            "platform": platform,
            "industry": industry,
            "audience_country": audience_country,
            "audience_age": audience_age
        }

        # Analyze
        try:
            result = await ai_engine.analyze_ad_v59(request_data, [])

            # Debug mode: Return full AI response
            if debug:
                return {
                    "success": True,
                    "debug": True,
                    "data": result,
                    "content_received": {
                        "type": content_type,
                        "length": len(content),
                        "first_50": content[:50],
                        "last_50": content[-50:]
                    }
                }

            # Normal mode: Return cleaned data
            return {
                "success": True,
                "data": result
            }

        except ValueError as e:
            # AI returned generic scores
            logger.error(f"❌ Generic score detected: {e}")
            raise HTTPException(
                status_code=502, 
                detail=f"AI returned generic scores. {str(e)}. Please retry."
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 Error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze/debug")
async def analyze_debug(
    ad_copy: Optional[str] = Form(None),
    video_script: Optional[str] = Form(None),
    platform: str = Form(...),
    industry: str = Form(...)
):
    """Debug endpoint - shows exactly what AI receives and returns"""
    return await analyze_endpoint(
        ad_copy=ad_copy, video_script=video_script,
        platform=platform, industry=industry,
        debug=True
    )
