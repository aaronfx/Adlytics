"""
ADLYTICS - Media Processing Service
Uses Pillow (PIL) for image analysis - pre-built wheels, no compilation needed
"""

from typing import Dict, Any, Optional, Tuple
from PIL import Image
import io
import math

class MediaProcessor:
    """Process images and videos using Pillow (no OpenCV compilation needed)"""

    def __init__(self):
        self.supported_image_formats = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        self.supported_video_formats = {'.mp4', '.mov', '.avi', '.webm'}

    def analyze_image(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Analyze image using Pillow
        Returns visual metrics without requiring OpenCV compilation
        """
        try:
            img = Image.open(io.BytesIO(image_bytes))
            width, height = img.size
            format_type = img.format
            mode = img.mode

            # Calculate brightness (simple average)
            if mode in ('RGB', 'RGBA', 'L'):
                gray_img = img.convert('L')
                pixels = list(gray_img.getdata())
                avg_brightness = sum(pixels) / len(pixels) if pixels else 128
                brightness_score = avg_brightness / 255.0
            else:
                brightness_score = 0.5

            # Detect if image has transparency
            has_transparency = mode in ('RGBA', 'P') or 'transparency' in img.info

            # Estimate visual complexity
            if mode in ('RGB', 'RGBA'):
                small_img = img.resize((100, 100))
                colors = small_img.getcolors(maxcolors=10000)
                color_count = len(colors) if colors else 10000
                complexity_score = min(color_count / 1000, 1.0)
            else:
                complexity_score = 0.5

            # Aspect ratio analysis
            aspect_ratio = width / height if height > 0 else 1.0
            is_mobile_friendly = 0.8 <= aspect_ratio <= 1.2

            # Platform-specific recommendations
            platform_recommendations = []
            if width < 600:
                platform_recommendations.append("Image may be too small for Facebook feed ads")
            if aspect_ratio > 2.0 or aspect_ratio < 0.5:
                platform_recommendations.append("Extreme aspect ratio may be cropped on Instagram")
            if brightness_score < 0.2:
                platform_recommendations.append("Very dark image - may lose detail on mobile")
            if brightness_score > 0.9:
                platform_recommendations.append("Very bright image - risk of overexposure")

            return {
                "width": width,
                "height": height,
                "aspect_ratio": round(aspect_ratio, 2),
                "format": format_type,
                "mode": mode,
                "brightness_score": round(brightness_score, 2),
                "complexity_score": round(complexity_score, 2),
                "has_transparency": has_transparency,
                "is_mobile_friendly": is_mobile_friendly,
                "file_size_kb": round(len(image_bytes) / 1024, 2),
                "platform_recommendations": platform_recommendations,
                "hook_strength_estimate": self._estimate_hook_strength(brightness_score, complexity_score, aspect_ratio),
                "text_readability_estimate": "Good" if brightness_score > 0.3 and brightness_score < 0.8 else "Poor"
            }

        except Exception as e:
            return {
                "error": str(e),
                "width": 0,
                "height": 0,
                "brightness_score": 0.5,
                "hook_strength_estimate": "Unable to analyze",
                "platform_recommendations": ["Image analysis failed - please check file format"]
            }

    def _estimate_hook_strength(self, brightness: float, complexity: float, aspect_ratio: float) -> str:
        """Estimate visual hook strength based on image metrics"""
        score = 0.5

        if 0.3 <= brightness <= 0.7:
            score += 0.2
        elif brightness < 0.1 or brightness > 0.9:
            score -= 0.2

        if complexity > 0.3:
            score += 0.15

        if 0.8 <= aspect_ratio <= 1.2:
            score += 0.15
        elif aspect_ratio > 2.0 or aspect_ratio < 0.5:
            score -= 0.1

        if score >= 0.7:
            return "Strong - high contrast, good composition"
        elif score >= 0.5:
            return "Moderate - acceptable but could be optimized"
        else:
            return "Weak - consider brighter/more focused imagery"

    def analyze_video(self, video_bytes: bytes) -> Dict[str, Any]:
        """
        Limited video analysis without OpenCV
        """
        file_size_mb = len(video_bytes) / (1024 * 1024)

        header = video_bytes[:20]
        format_guess = "unknown"

        if b'ftyp' in header:
            format_guess = "MP4"
        elif b'moov' in header or b'mdat' in header:
            format_guess = "QuickTime/MOV"
        elif header[:4] == b'RIFF' and b'AVI' in header[:12]:
            format_guess = "AVI"
        elif header[:4] == b'\x1a\x45\xdf\xa3':
            format_guess = "WebM/Matroska"

        return {
            "format_detected": format_guess,
            "file_size_mb": round(file_size_mb, 2),
            "analysis_type": "Limited (Pillow only - no video frames)",
            "note": "For full video analysis, install opencv-python-headless or use video processing API",
            "recommendations": [
                "Ensure first 3 seconds have strong visual hook",
                "Keep under 30 seconds for TikTok/Reels",
                "Add captions - 85% watch without sound",
                "Front-load key message in first 5 seconds"
            ],
            "hook_strength_estimate": "Manual review required",
            "platform_optimization": {
                "tiktok": "9:16 aspect ratio, fast cuts, trending audio",
                "instagram_reels": "9:16 or 4:5, text overlays, loop-friendly",
                "facebook": "1:1 or 4:5, captions required, slower pacing OK",
                "youtube_shorts": "9:16, 60s max, vertical text readable"
            }
        }

    def get_image_thumbnail(self, image_bytes: bytes, size: Tuple[int, int] = (300, 300)) -> bytes:
        """Generate thumbnail for preview"""
        try:
            img = Image.open(io.BytesIO(image_bytes))
            img.thumbnail(size, Image.Resampling.LANCZOS)

            output = io.BytesIO()
            img.save(output, format='PNG')
            return output.getvalue()
        except Exception:
            return b''


# Singleton instance
_media_processor: Optional[MediaProcessor] = None


def get_media_processor() -> MediaProcessor:
    """Get or create media processor singleton"""
    global _media_processor
    if _media_processor is None:
        _media_processor = MediaProcessor()
    return _media_processor
