# Film Investment Brief FastAPI Backend

This is the backend service that powers the deployment-focused Vercel frontend.

## What it does
- Exposes a POST /generate endpoint
- Accepts recipient email, timeframe, region, and categories
- Returns the exact JSON contract expected by the web app
- Includes:
  - briefing request/response models
  - mock production-safe generator
  - pluggable engine layer for your real live source pipeline
  - health endpoint
  - deployment files for Railway/Render-style hosting

## Endpoints

### GET /health
Returns service health status.

### POST /generate
Input:
{
  "recipientEmail": "person@example.com",
  "timeframe": "7",
  "region": "both",
  "categories": ["film", "tv", "new_media", "investment"]
}

Output:
{
  "generatedAt": "...",
  "timeframe": "7",
  "region": "both",
  "executiveSummary": [...],
  "items": [...],
  "html": "...",
  "text": "...",
  "subject": "Film Investment Brief"
}

## Local development
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Deployment
This service can be deployed on:
- Railway
- Render
- Fly.io
- any Docker-compatible host

Set your frontend env var:
PYTHON_BRIEFING_API_URL=https://your-backend.example.com/generate

## Replace mock engine with real engine
The current implementation uses a clean engine interface in:
- app/services/briefing_engine.py

You can replace the mock item generation there with:
- your RSS/feed aggregation
- scraping layer
- ranking logic
- plain-English summarization
- investor relevance logic
- HTML/text rendering
