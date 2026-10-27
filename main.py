import asyncio
import os

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

NEWS_URL = "https://newsapi.org/v2/top-headlines"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

app = FastAPI(title="FinNews AI", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

SYSTEM_PROMPT = (
    "You simplify financial news for beginners. Given an article, reply with:\n"
    "1) Summary: 2-3 plain-English sentences, no jargon.\n"
    "2) Why it matters: one sentence.\n"
    "3) Jargon explained: up to 3 terms with one-line definitions (skip if none).\n"
    "Only use facts from the article. Do not give investment advice."
)


def require_keys():
    if not NEWS_API_KEY or not GROQ_API_KEY:
        raise HTTPException(500, "Server missing NEWS_API_KEY or GROQ_API_KEY.")


async def fetch_news(client: httpx.AsyncClient, limit: int) -> list[dict]:
    try:
        r = await client.get(
            NEWS_URL,
            params={"category": "business", "language": "en",
                    "pageSize": limit, "apiKey": NEWS_API_KEY},
        )
    except httpx.HTTPError as e:
        raise HTTPException(502, f"Could not reach NewsAPI: {e}")
    if r.status_code != 200:
        raise HTTPException(502, f"NewsAPI error: {r.text[:200]}")
    articles = r.json().get("articles", [])
    return [a for a in articles if a.get("title") and a["title"] != "[Removed]"]


async def simplify(client: httpx.AsyncClient, text: str) -> str:
    try:
        r = await client.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            json={
                "model": GROQ_MODEL,
                "temperature": 0.3,
                "max_tokens": 400,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": text[:4000]},
                ],
            },
        )
        if r.status_code != 200:
            return f"(AI error {r.status_code})"
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"(AI unavailable: {e})"


@app.get("/health")
async def health():
    return {"status": "ok", "keys_configured": bool(NEWS_API_KEY and GROQ_API_KEY)}


@app.get("/api/news")
async def news(limit: int = Query(5, ge=1, le=10)):
    require_keys()
    async with httpx.AsyncClient(timeout=20) as client:
        return {"articles": await fetch_news(client, limit)}


@app.post("/api/simplify")
async def simplify_text(payload: dict):
    require_keys()
    text = (payload.get("text") or "").strip()
    if not text:
        raise HTTPException(400, "Field 'text' is required.")
    async with httpx.AsyncClient(timeout=30) as client:
        return {"simplified": await simplify(client, text)}


@app.get("/api/fetch-and-simplify")
async def fetch_and_simplify(limit: int = Query(5, ge=1, le=10)):
    require_keys()
    async with httpx.AsyncClient(timeout=30) as client:
        articles = await fetch_news(client, limit)
        texts = [
            f"{a['title']}\n{a.get('description') or ''}\n{a.get('content') or ''}"
            for a in articles
        ]
        summaries = await asyncio.gather(*(simplify(client, t) for t in texts))
    return {
        "results": [
            {"title": a["title"], "source": (a.get("source") or {}).get("name"),
             "url": a.get("url"), "publishedAt": a.get("publishedAt"),
             "simplified": s}
            for a, s in zip(articles, summaries)
        ]
    }
