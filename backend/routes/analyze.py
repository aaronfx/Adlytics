"""
ADLYTICS - Analysis Routes
Handles ad analysis API endpoint with proper error handling
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional, Dict, Any
import traceback

from backend.services.ai_engine import get_ai_engine
from backend.services.media_processor import get_media_processor

router = APIRouter()

@router.post("/analyze")
async def analyze_ad(
    ad_copy: Optional[str] = Form(None),
    video_script: Optional[str] = Form(None),
    platform: str = Form(...),
    country: str = Form(...),
    state: str = Form(...),
    age_bracket: str = Form(...),
    gender: str = Form(...),
    income: str = Form(...),
    education: str = Form(...),
    occupation: str = Form(...),
    psychographic: str = Form(...),
    pain_point: str = Form(...),
    tech_savviness: str = Form(...),
    purchase_style: str = Form(...),
    industry: str = Form(...),
    objective: str = Form(...),
    image: Optional[UploadFile] = File(None),
    video: Optional[UploadFile] = File(None)
) -> Dict[str, Any]:
    """
    Analyze ad copy/video script with AI
    Returns structured analysis with ROI forecast
    """
    try:
        # Validate at least one content type is provided
        if not ad_copy and not video_script:
            return {
                "success": False,
                "error": "Please provide either ad copy or video script",
                "behavior_summary": {"verdict": "No content provided", "launch_readiness": "0%"},
                "scores": {"overall": 0}
            }

        # Combine content for analysis
        combined_copy = ""
        content_type = []
        if ad_copy:
            combined_copy += f"AD COPY:\n{ad_copy}\n\n"
            content_type.append("Ad Copy")
        if video_script:
            combined_copy += f"VIDEO SCRIPT:\n{video_script}\n\n"
            content_type.append("Video Script")

        # Build rich audience description
        audience_description = f"""
{age_bracket} {gender} {occupation} with {education} in {state}, {country} ({income} income level).
Psychographic: {psychographic}. 
Primary pain point: {pain_point}.
Digital behavior: {tech_savviness} with technology.
Purchase style: {purchase_style}.
""".strip()

        # Process media if uploaded
        media_context = None
        if image:
            image_bytes = await image.read()
            processor = get_media_processor()
            media_context = processor.analyze_image(image_bytes)
            content_type.append("Image")

        if video:
            video_bytes = await video.read()
            processor = get_media_processor()
            video_analysis = processor.analyze_video(video_bytes)
            if media_context:
                media_context.update(video_analysis)
            else:
                media_context = video_analysis
            content_type.append("Video")

        # Get AI analysis
        engine = get_ai_engine()
        result = await engine.analyze(
            ad_copy=combined_copy.strip(),
            platform=platform,
            audience_description=audience_description,
            industry=industry,
            objective=objective,
            media_context=media_context
        )

        # Add metadata
        result["_meta"] = {
            "content_type": " + ".join(content_type),
            "platform": platform,
            "audience": f"{age_bracket} {occupation} in {country}"
        }

        return result

    except Exception as e:
        # Log the full error for debugging
        print(f"Analysis error: {str(e)}")
        print(traceback.format_exc())

        # Return structured error response (always JSON)
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "behavior_summary": {
                "micro_stop_rate": "Unknown",
                "scroll_stop_rate": "Unknown",
                "attention_retention": "Unknown",
                "trust_level": "Unknown",
                "click_probability": "Unknown",
                "post_click_bounce_risk": "Unknown",
                "failure_risk": "100%",
                "verdict": f"Analysis failed: {str(e)}",
                "primary_reason": "Backend error occurred",
                "launch_readiness": "0%"
            },
            "scores": {
                "overall": 0,
                "hook_strength": 0,
                "clarity": 0,
                "trust_building": 0,
                "cta_power": 0,
                "audience_alignment": 0,
                "cultural_resonance": 0,
                "decision_friction": 0,
                "predicted_lift_if_fixed": "+0%"
            },
            "critical_weaknesses": [{
                "issue": f"System error: {str(e)}",
                "behavior_impact": "Analysis could not be completed",
                "precise_fix": "Please check server logs or retry",
                "estimated_lift": "+0%"
            }],
            "improvements": ["Retry the analysis", "Check API configuration"],
            "improved_ad": {
                "headline": "[Error occurred]",
                "body_copy": ad_copy[:100] if ad_copy else "",
                "cta": "[Please retry]",
                "video_script_version": "[Please retry]"
            },
            "video_execution_analysis": {
                "is_video_script": "Unknown",
                "hook_delivery_strength": "Unable to assess",
                "speech_flow_quality": "Unable to assess",
                "visual_dependency": "Unable to assess",
                "delivery_risk": "Unable to assess",
                "biggest_execution_gap": str(e),
                "recommended_format": "talking head"
            },
            "roi_analysis": {
                "roi_potential": "UltraLow",
                "break_even_probability": "0%",
                "risk_classification": "High",
                "confidence_level": "Low",
                "confidence_reason": f"Error: {str(e)}",
                "key_metrics": {
                    "expected_ctr_range": "0% - 0%",
                    "realistic_cpc_range": "$0.00 - $0.00",
                    "conversion_rate_range": "0% - 0%"
                },
                "roi_scenarios": {
                    "worst_case": "Analysis failed",
                    "expected_case": "Analysis failed",
                    "best_case": "Analysis failed"
                },
                "primary_roi_lever": "Fix backend error",
                "biggest_financial_risk": str(e)
            }
        }
