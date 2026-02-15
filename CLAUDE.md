# CLAUDE.md - FOMC Stance Tracker

## Project Overview
FOMC Participant Stance Tracker - classifies Federal Reserve officials as hawkish or dovish based on recent news, speeches, and historical data. Produces an interactive Streamlit dashboard.

## Tech Stack
- **Python 3.11** with **Poetry** for dependency management
- **duckduckgo-search**: Free news search (no API key)
- **feedparser + BeautifulSoup**: Fed RSS feeds and speech scraping
- **Pandas**: Data manipulation
- **Streamlit + Plotly**: Interactive dashboard
- **Keyword-based NLP**: No heavy ML models required

## Key Commands
```bash
# Setup
poetry install && poetry shell

# Fetch latest data and classify stances
python fetch_data.py

# Preview participants only
python fetch_data.py --participants-only

# Fetch single participant
python fetch_data.py --name "Jerome Powell"

# Launch dashboard
streamlit run dashboard.py

# Run tests
pytest tests/
```

## Project Structure
```
fomc_tracker/           # Core package
  participants.py       # FOMC roster (19 members, metadata)
  news_fetcher.py       # DuckDuckGo + Fed RSS + BIS speeches data fetching
  fed_speeches.py       # Federal Reserve speech scraping
  stance_classifier.py  # Keyword-based hawkish/dovish classifier
  historical_data.py    # Historical stance storage + seed data
fetch_data.py           # CLI orchestrator
dashboard.py            # Streamlit dashboard
data/                   # Auto-created, stores fetched data + history
tests/                  # Unit tests
```

## Architecture
1. `participants.py` defines the FOMC roster (no dependencies)
2. `news_fetcher.py` + `fed_speeches.py` fetch data from web
3. `stance_classifier.py` scores text on -1.0 (dovish) to +1.0 (hawkish)
4. `historical_data.py` persists stances over time with seed data
5. `fetch_data.py` orchestrates fetch → classify → store
6. `dashboard.py` visualizes everything via Streamlit + Plotly

## Data Flow
```
DuckDuckGo News + Fed RSS + BIS Speeches → news_fetcher → JSON files in data/news/
                                              ↓
                              stance_classifier → scored stances
                                              ↓
                              historical_data → data/historical/stance_history.json
                                              ↓
                              dashboard.py → Streamlit charts
```

## Conventions
- Scores: -1.0 (very dovish) to +1.0 (very hawkish)
- Labels: "Dovish" (< -0.3), "Neutral" (-0.3 to 0.3), "Hawkish" (> 0.3)
- Data files: JSON, date-prefixed (`2026-02-15_Jerome_H_Powell.json`)
- Rate limiting: 1.5s between DuckDuckGo requests
