# FinNews AI – Financial News Simplifier

## Setup
1. Get keys: https://newsapi.org and https://console.groq.com
2. Backend:
   ```
   cd backend
   python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env      # then fill in your keys
   uvicorn main:app --reload
   ```
3. Frontend: `cd frontend && python -m http.server 5500`, open http://localhost:5500

## Endpoints
- `GET /health`
- `GET /api/news?limit=5`
- `POST /api/simplify` with `{"text": "..."}`
- `GET /api/fetch-and-simplify?limit=5`

Docs at http://localhost:8000/docs. Never commit `.env`.
