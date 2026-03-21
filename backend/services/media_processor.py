"""
ADLYTICS - Media Processor Service
Handles image and video analysis for ad creatives
"""

import cv2
import numpy as np
from typing import Dict, Any, Optional
import io

class MediaProcessor:
    def __init__(self):
        self.supported_image_formats = ['.jpg', '.jpeg', '.png', '.webp', '.bmp']
        self.supported_video_formats = ['.mp4', '.mov', '.avi', '.webm']

    def analyze_image(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Analyze image for ad creative insights
        Returns visual characteristics that affect ad performance
        """
        try:
            # Convert bytes to numpy array
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if img is None:
                return {"error": "Could not decode image"}

            height, width = img.shape[:2]

            # Color analysis
            color_analysis = self._analyze_colors(img)

            # Brightness/contrast
            brightness = self._analyze_brightness(img)

            # Text detection (rough heuristic)
            text_score = self._detect_text_regions(img)

            # Visual complexity
            complexity = self._analyze_complexity(img)

            # Face detection (for human element assessment)
            faces = self._detect_faces(img)

            return {
                "dimensions": f"{width}x{height}",
                "aspect_ratio": round(width / height, 2),
                "dominant_colors": color_analysis["dominant"],
                "brightness": brightness,
                "contrast": color_analysis["contrast"],
                "visual_complexity": complexity,
                "text_detected": text_score > 0.3,
                "faces_detected": len(faces),
                "platform_recommendations": self._platform_recs(width, height, brightness, complexity),
                "ad_readiness_score": self._calculate_readiness(width, height, brightness, complexity, text_score)
            }

        except Exception as e:
            return {"error": f"Image analysis failed: {str(e)}"}

    def analyze_video(self, video_bytes: bytes) -> Dict[str, Any]:
        """
        Analyze first 5 seconds of video for hook assessment
        """
        try:
            # Write to temp file (OpenCV needs file path for video)
            temp_path = "/tmp/temp_video.mp4"
            with open(temp_path, "wb") as f:
                f.write(video_bytes)

            cap = cv2.VideoCapture(temp_path)

            if not cap.isOpened():
                return {"error": "Could not open video"}

            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0

            # Analyze first 5 seconds (or full video if shorter)
            frames_to_analyze = min(int(fps * 5), total_frames)

            frame_scores = []
            faces_detected = 0
            brightness_changes = []

            prev_brightness = None

            for i in range(frames_to_analyze):
                ret, frame = cap.read()
                if not ret:
                    break

                # Analyze every 10th frame for performance
                if i % 10 == 0:
                    brightness = self._analyze_brightness(frame)
                    faces = self._detect_faces(frame)
                    faces_detected = max(faces_detected, len(faces))

                    if prev_brightness is not None:
                        brightness_changes.append(abs(brightness - prev_brightness))
                    prev_brightness = brightness

                    frame_scores.append({
                        "timestamp": round(i / fps, 1),
                        "brightness": brightness,
                        "faces": len(faces)
                    })

            cap.release()

            # Calculate hook indicators
            avg_brightness_change = np.mean(brightness_changes) if brightness_changes else 0
            hook_strength = "High" if avg_brightness_change > 20 or faces_detected > 0 else "Medium" if avg_brightness_change > 10 else "Low"

            return {
                "duration_seconds": round(duration, 1),
                "fps": round(fps, 1),
                "resolution": f"{int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}",
                "first_5s_hook_strength": hook_strength,
                "faces_in_opening": faces_detected,
                "visual_dynamics": "High" if avg_brightness_change > 25 else "Medium" if avg_brightness_change > 12 else "Low",
                "frame_samples": frame_scores[:5],  # First 5 sample frames
                "platform_notes": self._video_platform_notes(hook_strength, faces_detected, duration)
            }

        except Exception as e:
            return {"error": f"Video analysis failed: {str(e)}"}

    def _analyze_colors(self, img: np.ndarray) -> Dict[str, Any]:
        """Extract dominant colors and contrast"""
        # Convert to RGB for analysis
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Reshape for clustering
        pixels = rgb.reshape(-1, 3).astype(np.float32)

        # K-means for dominant colors
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        _, labels, centers = cv2.kmeans(pixels, 3, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)

        # Convert to hex
        dominant = []
        for center in centers:
            r, g, b = int(center[0]), int(center[1]), int(center[2])
            dominant.append(f"#{r:02x}{g:02x}{b:02x}")

        # Calculate contrast (std dev of brightness)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        contrast = round(float(np.std(gray)), 1)

        return {"dominant": dominant, "contrast": contrast}

    def _analyze_brightness(self, img: np.ndarray) -> str:
        """Assess overall brightness"""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        mean_brightness = np.mean(gray)

        if mean_brightness < 50:
            return "Very Dark"
        elif mean_brightness < 100:
            return "Dark"
        elif mean_brightness < 150:
            return "Medium"
        elif mean_brightness < 200:
            return "Bright"
        else:
            return "Very Bright"

    def _detect_text_regions(self, img: np.ndarray) -> float:
        """Heuristic for text detection using edge density"""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Edge detection
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])

        return float(edge_density)

    def _analyze_complexity(self, img: np.ndarray) -> str:
        """Assess visual complexity"""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Edge density as complexity proxy
        edges = cv2.Canny(gray, 50, 150)
        edge_ratio = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])

        if edge_ratio < 0.02:
            return "Minimal"
        elif edge_ratio < 0.05:
            return "Simple"
        elif edge_ratio < 0.1:
            return "Moderate"
        elif edge_ratio < 0.2:
            return "Complex"
        else:
            return "Very Complex"

    def _detect_faces(self, img: np.ndarray) -> list:
        """Detect faces using Haar cascade"""
        try:
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            return faces
        except:
            return []

    def _platform_recs(self, width: int, height: int, brightness: str, complexity: str) -> Dict[str, str]:
        """Platform-specific recommendations"""
        aspect = width / height

        recs = {}

        # TikTok/Reels (9:16)
        if aspect < 0.6:
            recs["vertical_video"] = "Optimal for TikTok/Reels"
        else:
            recs["vertical_video"] = "Crop to 9:16 for TikTok/Reels"

        # Instagram (1:1 or 4:5)
        if 0.9 < aspect < 1.1:
            recs["instagram_feed"] = "Perfect for Instagram feed"
        else:
            recs["instagram_feed"] = "Consider 1:1 square crop"

        # Facebook (varies)
        recs["facebook"] = "Works across placements"

        # Brightness note
        if brightness in ["Very Dark", "Dark"]:
            recs["brightness"] = "May lose impact on mobile in bright environments"

        return recs

    def _calculate_readiness(self, width: int, height: int, brightness: str, complexity: str, text_score: float) -> int:
        """Calculate ad readiness score 0-100"""
        score = 50

        # Resolution bonus
        if width >= 1080:
            score += 15
        elif width >= 720:
            score += 10

        # Brightness balance
        if brightness == "Medium":
            score += 15
        elif brightness in ["Bright", "Dark"]:
            score += 5

        # Complexity balance
        if complexity == "Moderate":
            score += 10
        elif complexity == "Simple":
            score += 5

        # Text presence (usually good for ads)
        if text_score > 0.1:
            score += 10

        return min(100, score)

    def _video_platform_notes(self, hook_strength: str, faces: int, duration: float) -> Dict[str, str]:
        """Video-specific platform notes"""
        notes = {}

        if hook_strength == "High":
            notes["tiktok"] = "Strong visual dynamics — will stop scroll"
            notes["youtube"] = "Good retention potential"
        else:
            notes["tiktok"] = "Consider stronger opening hook (brightness change or face)"

        if faces > 0:
            notes["facebook"] = "Human element increases engagement"

        if duration < 15:
            notes["instagram_reels"] = "Short format optimal"
        elif duration > 60:
            notes["youtube"] = "Better suited for long-form"

        return notes
