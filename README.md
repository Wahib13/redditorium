# Trend Engine

## Summary

A personal data-driven project that collects and analyzes activity across online content feeds to understand and summarize emerging trends. The tool aggregates posts, discussions, and articles from
multiple sources to highlight what’s most relevant and interesting.
Main goal: reduce doom-scrolling and explore how trending topics evolve over time.

I built this tool to reduce doom-scrolling and help myself stay informed efficiently. I get a daily digest of what’s trending and what I actually care about.

## Data Model

https://dbdiagram.io/d/FeedScope-68efcd9d2e68d21b41a3386f

## Installation

1. Clone the repository

```commandline
git clone https://github.com/Wahib13/trend-engine
cd trend-engine
```

2. Install dependencies
```commandline
pip install -r requirements.txt
```

3. Environment setup:
Make a copy of the example environment file:
```commandline
cp .env.example .env
```

# Running Tests
```commandline
cd src/
python -m pytest
```

# Running Ingestion
```commandline
cd src/
python -m scripts.run_ingestion
```