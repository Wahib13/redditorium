# Trend Engine

## Summary

Trend Engine is a personal data-driven project focused on **collecting and organizing articles from online content feeds** in order to better understand what topics are being discussed across sources.

At its current stage, the project:

- Ingests articles from predefined RSS feeds (BBC, The Guardian)
- Fetches full article text using newspaper3k
- Extracts keywords from article text using YAKE
- Exposes articles and keywords via a REST API

The broader goal is to **reduce doom-scrolling** by creating a clean, structured view of incoming content, surfacing what's relevant through keyword-based grouping and (eventually) user subscriptions to keywords.

## Motivation

I built this tool to help myself stay informed without constantly scrolling through feeds. Instead of consuming everything in real time, the idea is to collect content in the background and surface what's relevant in a more deliberate, digestible way.

## Data Model

https://dbdiagram.io/d/FeedScope-68efcd9d2e68d21b41a3386f

## Installation

1. Clone the repository

```bash
git clone https://github.com/Wahib13/trend-engine
cd trend-engine
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Set up environment files

```bash
cp .env.example .env
cp ui/.env.example ui/.env
```

4. Run database migrations

```bash
cd src/
alembic upgrade head
```

5. Seed the database with default sources and feeds

```bash
python -m scripts.init_db
```

Sources and feeds are defined in `src/seeds.yaml` — edit that file to add or remove feeds.

## Running the Pipeline

```bash
cd src/

# Fetch article titles from RSS feeds
python -m scripts.fetch_feed_data

# Fetch full article text
python -m scripts.fetch_content
```

## Running Tests

```bash
cd src/
python -m pytest
```

## Running the Frontend

```bash
cd ui/
npm install
npm run dev
```

## Running with Docker

```bash
docker compose up
```
