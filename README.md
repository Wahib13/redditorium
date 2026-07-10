# Trend Engine

## Summary

Trend Engine is a personal project that collects articles from RSS feeds and surfaces trending topics in a clean, live-updating UI — without the noise of doom-scrolling.

It currently:

- Ingests articles from RSS feeds (BBC, The Guardian) across topics (Politics, Technology, Business, Health)
- Fetches full article text and generates semantic embeddings (sentence-transformers)
- Extracts keywords from article titles using KeyBERT, always including the feed topic
- Exposes keywords and articles via a REST API with WebSocket live updates
- Provides a React frontend that groups articles by keyword, filters by source, and supports semantic search

## Motivation

I built this to stay informed without constantly scrolling through feeds. Content is collected in the background; the UI surfaces what's relevant in a structured, deliberate way. As new articles are processed, the sidebar updates live without interrupting whatever you're reading.

## Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, SQLAlchemy, PostgreSQL + pgvector |
| Keyword extraction | KeyBERT |
| Semantic search | sentence-transformers (384-dim), pgvector cosine distance |
| Frontend | React, TypeScript, Vite, React Query |
| Auth | JWT (python-jose) |

## Installation

1. Clone the repository

```bash
git clone https://github.com/Wahib13/trend-engine
cd trend-engine
```

2. Install Python dependencies

```bash
pip install -r requirements.txt
```

3. Set up environment files

```bash
cp .env.example .env
cp ui/.env.example ui/.env
```

Edit `.env` — at minimum set `DATABASE_CONNECTION_STRING` (PostgreSQL with pgvector) and `JWT_SECRET_KEY`.

4. Run database migrations

```bash
cd src/
alembic upgrade head
```

5. Seed the database with default sources and feeds

```bash
python -m scripts.init_db
```

Sources and feeds are defined in `src/seeds.yaml` — edit that file to add or remove feeds, then re-run `init_db`.

## Running the Pipeline

```bash
cd src/

# Full pipeline: fetch feeds → embed → extract keywords → notify UI live
python -m scripts.run_pipeline --api-base http://localhost:8081

# Or run individual steps
python -m scripts.fetch_feed_data   # fetch RSS entries
python -m scripts.fetch_content     # download full article text
```

The pipeline notifies the API after each keyword link. If the API is running, connected browsers update in real time via WebSocket.

## Running the API

```bash
cd src/
uvicorn api.main:app --reload
```

## Running the Frontend

```bash
cd ui/
npm install
npm run dev
```

## Running with Docker

The `api` and `ui` services in `docker-compose.yml` are currently commented out, so this starts only the Postgres + pgvector database. Run the API and frontend with the commands above.

```bash
docker compose up
```

## Running Tests

```bash
cd src/
python -m pytest
```
