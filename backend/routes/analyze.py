"""
ADLYTICS - Analysis Routes
Handles ad analysis API endpoint with proper error handling and field mapping
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
    audience_country: str = Form(...),
    audience_region: Optional[str] = Form(""),
    audience_age: str = Form(...),
    audience_gender: Optional[str] = Form(""),
    audience_income: Optional[str] = Form(""),
    audience_education: Optional[str] = Form(""),
    audience_occupation: Optional[str] = Form(""),
    audience_psychographic: Optional[str] = Form(""),
    audience_pain_point: Optional[str] = Form(""),
    tech_savviness: Optional[str] = Form("medium"),
    purchase_behavior: Optional[str] = Form(""),
    industry: str = Form(...),
    objective: str = Form(...),
    image: Optional[UploadFile] = File(None),
    video: Optional[UploadFile] = File(None)
) -> Dict[str, Any]:
    """
    Analyze ad copy/video script with AI
    Returns structured analysis with ROI forecast
    
    FRONTEND FIELD MAPPING:
    - audienceCountry -> audience_country
    - audienceRegion -> audience_region  
    - audienceAge -> audience_age
    - audienceGender -> audience_gender
    - audienceIncome -> audience_income
    - audienceEducation -> audience_education
    - audienceOccupation -> audience_occupation
    - audiencePsychographic -> audience_psychographic
    - audiencePainPoint -> audience_pain_point
    - techSavviness -> tech_savviness
    - purchaseBehavior -> purchase_behavior
    """
    try:
        # Validate at least one content type is provided
        if not ad_copy and not video_script:
            return {
                "success": False,
                "analysis": {
                    "behavior_summary": {
                        "verdict": "No content provided - please enter ad copy or video script",
                        "launch_readiness": "0%",
                        "failure_risk": "100%"
                    },
                    "scores": {"overall": 0}
                },
                "error": "Please provide either ad copy or video script"
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
Target: {audience_age} {audience_gender or 'any gender'} {audience_occupation or 'professional'} 
Location: {audience_region or 'major city'}, {audience_country}
Education: {audience_education or 'not specified'}
Income: {audience_income or 'not specified'}
Psychographic: {audience_psychographic or 'not specified'}
Pain Point: {audience_pain_point or 'not specified'}
Tech Level: {tech_savviness}
Purchase Style: {purchase_behavior or 'not specified'}
""".strip()

        # Process media if uploaded
        media_context = None
        if image and image.filename:
            try:
                image_bytes = await image.read()
                if len(image_bytes) > 0:
                    processor = get_media_processor()
                    media_context = processor.analyze_image(image_bytes)
                    content_type.append("Image")
            except Exception as media_err:
                print(f"Image processing error: {media_err}")
                media_context = {"error": str(media_err)}

        if video and video.filename:
            try:
                video_bytes = await video.read()
                if len(video_bytes) > 0:
                    processor = get_media_processor()
                    video_analysis = processor.analyze_video(video_bytes)
                    if media_context:
                        media_context.update(video_analysis)
                    else:
                        media_context = video_analysis
                    content_type.append("Video")
            except Exception as media_err:
                print(f"Video processing error: {media_err}")
                if media_context:
                    media_context["video_error"] = str(media_err)
                else:
                    media_context = {"video_error": str(media_err)}

        # Get AI analysis
        engine = get_ai_engine()
        result = await engine.analyze_ad(
            ad_copy=combined_copy.strip(),
            platform=platform,
            audience_description=audience_description,
            industry=industry,
            objective=objective,
            media_context=media_context
        )

        # Wrap in success response format expected by frontend
        return {
            "success": True,
            "analysis": result,
            "audience_parsed": audience_description.replace("\n", " ").strip(),
            "content_type": " + ".join(content_type),
            "platform": platform
        }

    except Exception as e:
        # Log the full error for debugging
        print(f"Analysis error: {str(e)}")
        print(traceback.format_exc())

        # Return structured error response that frontend can handle
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "analysis": {
                "behavior_summary": {
                    "micro_stop_rate": "Unknown",
                    "scroll_stop_rate": "Unknown",
                    "attention_retention": "Unknown",
                    "trust_level": "Unknown",
                    "click_probability": "Unknown",
                    "post_click_bounce_risk": "Unknown",
                    "failure_risk": "100%",
                    "verdict": f"Analysis failed: {str(e)[:100]}",
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
                    "issue": f"System error: {str(e)[:100]}",
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
                    "biggest_execution_gap": str(e)[:100],
                    "recommended_format": "talking head"
                },
                "roi_analysis": {
                    "roi_potential": "UltraLow",
                    "break_even_probability": "0%",
                    "risk_classification": "High",
                    "confidence_level": "Low",
                    "confidence_reason": f"Error: {str(e)[:100]}",
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
                    "biggest_financial_risk": str(e)[:100]
                }
            }
        }
