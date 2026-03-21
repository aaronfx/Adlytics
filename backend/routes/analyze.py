"""
ADLYTICS - Analysis Routes v4.0
Handles ad analysis API endpoint with v4.0 features:
- Line-by-line analysis
- Ad variant generation
- Winner prediction
- ROI comparison
- Run decision engine
- Competitor advantage analysis
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional, Dict, Any, List
import traceback

from backend.services.ai_engine import get_ai_engine
from backend.services.media_processor import get_media_processor

router = APIRouter()


def validate_v4_response(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and ensure all v4.0 fields are present in AI response.
    If fields are missing, populate with sensible defaults.
    """
    
    # Ensure line_by_line_analysis exists and is valid
    if "line_by_line_analysis" not in analysis or not isinstance(analysis["line_by_line_analysis"], list):
        analysis["line_by_line_analysis"] = []
    
    # Ensure ad_variants exists (5-10 variants expected)
    if "ad_variants" not in analysis or not isinstance(analysis["ad_variants"], list):
        analysis["ad_variants"] = []
    
    # Validate each variant has required fields
    for i, variant in enumerate(analysis.get("ad_variants", [])):
        if not isinstance(variant, dict):
            analysis["ad_variants"][i] = {
                "id": i + 1,
                "angle": "Unknown",
                "hook": "",
                "copy": "",
                "predicted_score": 50,
                "roi_potential": "Medium",
                "reason": "Variant data incomplete"
            }
        else:
            # Ensure all variant fields exist
            variant.setdefault("id", i + 1)
            variant.setdefault("angle", f"Variant {i + 1}")
            variant.setdefault("hook", "")
            variant.setdefault("copy", "")
            variant.setdefault("predicted_score", 50)
            variant.setdefault("roi_potential", "Medium")
            variant.setdefault("reason", "")
    
    # Ensure winner_prediction exists
    if "winner_prediction" not in analysis or not isinstance(analysis["winner_prediction"], dict):
        analysis["winner_prediction"] = {
            "best_variant_id": 1,
            "reason": "Analysis incomplete - default selection",
            "expected_lift": "+0%",
            "confidence": "Low"
        }
    else:
        winner = analysis["winner_prediction"]
        winner.setdefault("best_variant_id", 1)
        winner.setdefault("reason", "No prediction available")
        winner.setdefault("expected_lift", "+0%")
        winner.setdefault("confidence", "Low")
    
    # Ensure roi_comparison exists
    if "roi_comparison" not in analysis or not isinstance(analysis["roi_comparison"], list):
        analysis["roi_comparison"] = []
    
    # Validate ROI comparison entries
    for i, comp in enumerate(analysis.get("roi_comparison", [])):
        if not isinstance(comp, dict):
            analysis["roi_comparison"][i] = {
                "variant_id": i + 1,
                "roi_potential": "Unknown",
                "risk": "Unknown",
                "summary": "Comparison unavailable"
            }
        else:
            comp.setdefault("variant_id", i + 1)
            comp.setdefault("roi_potential", "Unknown")
            comp.setdefault("risk", "Unknown")
            comp.setdefault("summary", "")
    
    # Ensure run_decision exists
    if "run_decision" not in analysis or not isinstance(analysis["run_decision"], dict):
        analysis["run_decision"] = {
            "should_run": "Only after fixes",
            "reason": "Analysis incomplete - manual review required",
            "risk_level": "High"
        }
    else:
        decision = analysis["run_decision"]
        decision.setdefault("should_run", "Only after fixes")
        decision.setdefault("reason", "No decision reason provided")
        decision.setdefault("risk_level", "Unknown")
    
    # Ensure competitor_advantage exists
    if "competitor_advantage" not in analysis or not isinstance(analysis["competitor_advantage"], dict):
        analysis["competitor_advantage"] = {
            "why_user_might_choose_competitor": "Unable to analyze",
            "what_competitor_is_doing_better": "Unable to analyze",
            "execution_difference": "Unable to analyze",
            "how_to_outperform": "Focus on unique value proposition"
        }
    else:
        comp = analysis["competitor_advantage"]
        comp.setdefault("why_user_might_choose_competitor", "Unknown")
        comp.setdefault("what_competitor_is_doing_better", "Unknown")
        comp.setdefault("execution_difference", "Unknown")
        comp.setdefault("how_to_outperform", "Differentiate clearly")
    
    # Ensure video_execution_analysis has v4 fields
    if "video_execution_analysis" not in analysis:
        analysis["video_execution_analysis"] = {}
    
    video = analysis["video_execution_analysis"]
    if not isinstance(video, dict):
        analysis["video_execution_analysis"] = {
            "hook_delivery_strength": "Unable to assess",
            "speech_flow_quality": "Unable to assess",
            "pattern_interrupt_strength": "Unable to assess",
            "visual_dependency": "Medium",
            "delivery_risk": "Unable to assess",
            "recommended_format": "talking head",
            "execution_gaps": [],
            "exact_fix_direction": ""
        }
    else:
        # Add v4 video fields if missing
        video.setdefault("hook_delivery_strength", "Unable to assess")
        video.setdefault("speech_flow_quality", "Unable to assess")
        video.setdefault("pattern_interrupt_strength", "Unable to assess")
        video.setdefault("visual_dependency", "Medium")
        video.setdefault("delivery_risk", "Unable to assess")
        video.setdefault("recommended_format", "talking head")
        video.setdefault("execution_gaps", [])
        video.setdefault("exact_fix_direction", "")
    
    # Ensure roi_analysis has optimization_priority
    if "roi_analysis" not in analysis:
        analysis["roi_analysis"] = {}
    
    roi = analysis["roi_analysis"]
    if isinstance(roi, dict):
        roi.setdefault("optimization_priority", "Review all metrics")
    
    return analysis


def generate_line_by_line_from_copy(ad_copy: str) -> List[Dict[str, Any]]:
    """
    Fallback: Generate basic line-by-line analysis if AI doesn't provide it.
    Splits ad copy by newlines or sentences.
    """
    if not ad_copy:
        return []
    
    # Split by newlines first, then by sentences if no newlines
    lines = [line.strip() for line in ad_copy.split('\n') if line.strip()]
    if len(lines) <= 1:
        # Split by sentence endings
        import re
        lines = [s.strip() for s in re.split(r'[.!?]+', ad_copy) if s.strip()]
    
    return [
        {
            "line": line[:100] + "..." if len(line) > 100 else line,
            "issue": None,
            "why_it_fails": None,
            "precise_fix": None,
            "impact": None
        }
        for line in lines[:20]  # Limit to 20 lines
    ]


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
    Analyze ad copy/video script with AI v4.0
    Returns structured analysis with:
    - Line-by-line breakdown
    - 5-10 generated ad variants
    - Winner prediction
    - ROI comparison
    - Run decision
    - Competitor analysis
    
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
                    "scores": {"overall": 0},
                    "line_by_line_analysis": [],
                    "ad_variants": [],
                    "winner_prediction": {
                        "best_variant_id": 1,
                        "reason": "No content to analyze",
                        "expected_lift": "+0%",
                        "confidence": "Low"
                    },
                    "roi_comparison": [],
                    "run_decision": {
                        "should_run": "No",
                        "reason": "No ad content provided",
                        "risk_level": "High"
                    },
                    "competitor_advantage": {
                        "why_user_might_choose_competitor": "N/A",
                        "what_competitor_is_doing_better": "N/A",
                        "execution_difference": "N/A",
                        "how_to_outperform": "Provide ad content first"
                    }
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

        # Validate and ensure v4.0 fields are present
        result = validate_v4_response(result)
        
        # Fallback: Generate line-by-line if AI didn't provide it
        if not result.get("line_by_line_analysis") and (ad_copy or video_script):
            content_to_analyze = video_script if video_script else ad_copy
            result["line_by_line_analysis"] = generate_line_by_line_from_copy(content_to_analyze)
        
        # Ensure we have at least some ad variants
        if not result.get("ad_variants"):
            # Generate basic variants from the original
            result["ad_variants"] = [
                {
                    "id": 1,
                    "angle": "Original",
                    "hook": ad_copy[:50] + "..." if ad_copy and len(ad_copy) > 50 else (ad_copy or "N/A"),
                    "copy": ad_copy or video_script or "",
                    "predicted_score": result.get("scores", {}).get("overall", 50),
                    "roi_potential": result.get("roi_analysis", {}).get("roi_potential", "Medium"),
                    "reason": "Original ad submitted for analysis"
                }
            ]
        
        # Ensure winner_prediction references a valid variant
        winner_id = result.get("winner_prediction", {}).get("best_variant_id", 1)
        valid_variant_ids = [v.get("id") for v in result.get("ad_variants", [])]
        if valid_variant_ids and winner_id not in valid_variant_ids:
            # Pick the highest scoring variant as winner
            best_variant = max(result["ad_variants"], key=lambda x: x.get("predicted_score", 0))
            result["winner_prediction"]["best_variant_id"] = best_variant["id"]
            result["winner_prediction"]["reason"] = f"Selected variant {best_variant['id']} with highest predicted score"
        
        # Ensure roi_comparison matches ad_variants
        if not result.get("roi_comparison") and result.get("ad_variants"):
            result["roi_comparison"] = [
                {
                    "variant_id": v["id"],
                    "roi_potential": v.get("roi_potential", "Medium"),
                    "risk": "Medium",
                    "summary": f"Variant {v['id']}: {v.get('angle', 'Unknown angle')}"
                }
                for v in result["ad_variants"]
            ]

        # Wrap in success response format expected by frontend
        return {
            "success": True,
            "analysis": result,
            "audience_parsed": audience_description.replace("\n", " ").strip(),
            "content_type": " + ".join(content_type),
            "platform": platform,
            "v4_features": {
                "line_by_line_analysis": len(result.get("line_by_line_analysis", [])) > 0,
                "ad_variants_count": len(result.get("ad_variants", [])),
                "winner_prediction": result.get("winner_prediction", {}).get("best_variant_id") is not None,
                "roi_comparison": len(result.get("roi_comparison", [])) > 0,
                "run_decision": result.get("run_decision", {}).get("should_run") is not None,
                "competitor_analysis": result.get("competitor_advantage", {}).get("how_to_outperform") is not None
            }
        }

    except Exception as e:
        # Log the full error for debugging
        print(f"Analysis error: {str(e)}")
        print(traceback.format_exc())

        # Return structured error response with v4.0 structure
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
                "phase_breakdown": {
                    "micro_stop_0_1s": "Unable to assess",
                    "scroll_stop_1_2s": "Unable to assess",
                    "attention_2_5s": "Unable to assess",
                    "trust_evaluation": "Unable to assess",
                    "click_and_post_click": "Unable to assess"
                },
                "line_by_line_analysis": [
                    {
                        "line": "Full content",
                        "issue": "Analysis failed",
                        "why_it_fails": str(e)[:100],
                        "precise_fix": "Retry analysis",
                        "impact": "+0%"
                    }
                ],
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
                "variations": {
                    "power_hooks": [],
                    "high_conversion_ctas": [],
                    "strongest_angles": []
                },
                "persona_reactions": [{
                    "persona": "General User",
                    "reaction": "Unable to simulate",
                    "exact_quote": "..."
                }],
                "video_execution_analysis": {
                    "hook_delivery_strength": "Unable to assess",
                    "speech_flow_quality": "Unable to assess",
                    "pattern_interrupt_strength": "Unable to assess",
                    "visual_dependency": "Medium",
                    "delivery_risk": "Unable to assess",
                    "recommended_format": "talking head",
                    "execution_gaps": ["Analysis failed"],
                    "exact_fix_direction": "Retry analysis"
                },
                "post_click_prediction": "Unable to predict",
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
                    "biggest_financial_risk": str(e)[:100],
                    "optimization_priority": "Resolve system error"
                },
                "ad_variants": [
                    {
                        "id": 1,
                        "angle": "Original (Error State)",
                        "hook": ad_copy[:50] if ad_copy else "N/A",
                        "copy": ad_copy or "",
                        "predicted_score": 0,
                        "roi_potential": "UltraLow",
                        "reason": "Analysis failed - using original"
                    }
                ],
                "winner_prediction": {
                    "best_variant_id": 1,
                    "reason": "Analysis failed - default to original",
                    "expected_lift": "+0%",
                    "confidence": "Low"
                },
                "roi_comparison": [
                    {
                        "variant_id": 1,
                        "roi_potential": "UltraLow",
                        "risk": "High",
                        "summary": "Analysis failed - cannot compare"
                    }
                ],
                "run_decision": {
                    "should_run": "No",
                    "reason": f"System error: {str(e)[:100]}",
                    "risk_level": "High"
                },
                "competitor_advantage": {
                    "why_user_might_choose_competitor": "Unable to analyze",
                    "what_competitor_is_doing_better": "Unable to analyze",
                    "execution_difference": "Unable to analyze",
                    "how_to_outperform": "Fix system error first"
                }
            }
        }
