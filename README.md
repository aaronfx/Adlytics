# ADLYTICS — AI Ad Pre-Validation & ROI Simulator

A production-ready MVP that simulates how real humans react to ads, then delivers brutal truth about whether they'll make or lose money.

![ADLYTICS](https://img.shields.io/badge/ADLYTICS-AI%20Ad%20Validation-purple)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green)
![Python](https://img.shields.io/badge/Python-3.11-blue)

## 🚀 Features

- **5-Persona Simulation**: Lagos scroller, Abuja professional, UK compliance officer, US buyer, and more
- **Behavioral Phases**: Micro-stop → Scroll-stop → Attention → Trust → Click analysis
- **ROI Forecasting**: Conservative, probabilistic predictions with risk classification
- **Smart Rewrite**: Platform-optimized ad variations and high-converting CTAs
- **Media Analysis**: Computer vision for image/video creative assessment
- **Real-time Results**: Complete analysis in 30 seconds

## 📁 Project Structure

```
.
├── backend/
│   ├── main.py                 # FastAPI entry point
│   ├── routes/
│   │   └── analyze.py          # Main analysis endpoint
│   └── services/
│       ├── ai_engine.py        # OpenAI integration
│       └── media_processor.py  # CV analysis
├── frontend/
│   ├── index.html              # Landing page
│   ├── app.html                # Analysis dashboard
│   └── js/
│       └── analyzer.js         # Frontend logic
├── requirements.txt            # Python dependencies
├── render.yaml                 # Render deployment config
└── .env.example                # Environment variables template
```

## 🛠️ Local Development

### Prerequisites

- Python 3.11+
- OpenAI API key

### Setup

1. **Clone and navigate**:
```bash
cd adlytics
```

2. **Create virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure environment**:
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

5. **Run backend**:
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

6. **Serve frontend** (in new terminal):
```bash
cd frontend
python -m http.server 3000
```

7. **Open**:
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

## 🌐 Deploy on Render

### One-Click Deploy

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

### Manual Deploy

1. **Push to GitHub**:
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/adlytics.git
git push -u origin main
```

2. **Create services on Render**:
   - Go to [dashboard.render.com](https://dashboard.render.com)
   - Click "New +" → "Blueprint"
   - Connect your GitHub repo
   - Render will read `render.yaml` and create both services

3. **Add environment variable**:
   - In the `adlytics-api` service, go to Environment
   - Add `OPENAI_API_KEY` with your key
   - Redeploy if needed

4. **Access**:
   - Frontend: `https://adlytics-frontend.onrender.com`
   - API: `https://adlytics-api.onrender.com`

## 📡 API Usage

### Analyze Endpoint

```bash
curl -X POST "https://adlytics-api.onrender.com/api/analyze" \
  -H "Content-Type: multipart/form-data" \
  -F "ad_copy=Turn ₦50,000 into ₦500,000 in 7 days" \
  -F "platform=tiktok" \
  -F "audience=Nigerian+professionals" \
  -F "industry=finance" \
  -F "objective=conversions"
```

### Response Structure

```json
{
  "success": true,
  "analysis": {
    "behavior_summary": {
      "micro_stop_rate": "Low",
      "scroll_stop_rate": "Low",
      "verdict": "Dies in <1s",
      "launch_readiness": "6%"
    },
    "scores": {
      "overall": 11,
      "hook_strength": 8,
      "trust_building": 3
    },
    "improved_ad": {
      "headline": "We Show You Our Losing Trades Too.",
      "body_copy": "Most Forex signal groups only post wins...",
      "cta": "See This Week's Trades Free"
    },
    "roi_analysis": {
      "roi_potential": "Ultra Low",
      "break_even_probability": "4%",
      "risk_classification": "High"
    }
  }
}
```

## 🧠 AI Engine

The system uses **GPT-4o Mini** via OpenAI API with:

- **Strict JSON mode**: Guaranteed parseable responses
- **Retry logic**: Automatic retry on timeout
- **Timeout handling**: 30-second request limit
- **Error recovery**: Graceful degradation with defaults

### System Prompt

The AI embodies 5 expert personas simultaneously:
1. Performance marketing strategist
2. Behavioral psychologist
3. Direct-response copywriter
4. Real-user reaction simulator
5. Conservative ROI forecaster

## 🖼️ Media Processing

### Image Analysis (OpenCV)

- Brightness/contrast assessment
- Dominant color extraction
- Face detection (human element)
- Visual complexity scoring
- Text region detection
- Platform-specific recommendations

### Video Analysis

- First 5-second hook assessment
- Frame-by-frame brightness tracking
- Face detection in opening
- Visual dynamics scoring
- Platform optimization notes

## 🎯 Use Cases

- **Performance Marketers**: Pre-validate before spending
- **Ad Agencies**: Client pitch validation
- **E-commerce**: Product launch testing
- **SaaS**: Landing page optimization
- **Forex/Crypto**: Compliance-aware copy checking

## ⚠️ Important Notes

1. **API Costs**: Each analysis uses ~2K tokens (~$0.002-0.004 per request on GPT-4o Mini)
2. **Rate Limits**: Implement client-side rate limiting for production
3. **File Limits**: 10MB images, 50MB videos
4. **Not Financial Advice**: ROI predictions are simulations, not guarantees

## 🔧 Customization

### Change AI Model

Edit `backend/services/ai_engine.py`:
```python
self.model = "gpt-4o"  # Upgrade for better analysis
```

### Add New Platforms

Edit `backend/routes/analyze.py`:
```python
platforms.append({"id": "snapchat", "name": "Snapchat", "focus": "Ephemeral content"})
```

### Modify Personas

Edit the system prompt in `ai_engine.py` to add/remove personas.

## 📄 License

MIT License — Built for performance marketers worldwide.

---

**Built with FastAPI + Tailwind + OpenAI + Render**
