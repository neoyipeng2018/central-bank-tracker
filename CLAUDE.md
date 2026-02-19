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
  defaults.py           # All default config values (upstream truth)
  config.py             # Config loader (merges local/ overrides)
  loader.py             # Auto-discovers local/ extension modules
  participants.py       # FOMC roster (19 members, metadata)
  news_fetcher.py       # DuckDuckGo + Fed RSS + BIS speeches data fetching
  fed_speeches.py       # Federal Reserve speech scraping
  stance_classifier.py  # Keyword-based hawkish/dovish classifier
  historical_data.py    # Historical stance storage + seed data
  policy_signal.py      # Vote-weighted signal + implied rate action
  fred_data.py          # FRED economic indicator integration
  meeting_calendar.py   # FOMC meeting schedule
fetch_data.py           # CLI orchestrator
dashboard.py            # Streamlit dashboard
generate_html.py        # Standalone HTML report generator
local.example/          # Example local overrides (copy to local/)
local/                  # Fork-specific overrides (gitignored upstream)
data/                   # Auto-created, stores fetched data + history
tests/                  # Unit tests
```

## Architecture
1. `participants.py` defines the FOMC roster (no dependencies)
2. `news_fetcher.py` + `fed_speeches.py` fetch data from web
3. `stance_classifier.py` scores text on -5.0 (dovish) to +5.0 (hawkish)
   - Routing: registered plugins → Cerebras → Gemini → OpenAI → keyword fallback
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
- Scores: -5.0 (very dovish) to +5.0 (very hawkish)
- Labels: "Dovish" (< -1.5), "Neutral" (-1.5 to 1.5), "Hawkish" (> 1.5)
- Data files: JSON, date-prefixed (`2026-02-15_Jerome_H_Powell.json`)
- Rate limiting: 1.5s between DuckDuckGo requests
- All configurable values live in `fomc_tracker/defaults.py`

## Configuration & Fork Customisation (`local/` system)

The codebase is designed to be forked without merge conflicts. All tuneable
values (thresholds, weights, URLs, colours) live in `fomc_tracker/defaults.py`.
Fork users override them by creating a `local/` directory (gitignored upstream):

```bash
# Quick start for fork users
cp -r local.example local
# Edit local/config.py, local/sources.py, etc.
```

### How it works
1. `fomc_tracker/defaults.py` — upstream defaults (single source of truth)
2. `fomc_tracker/config.py` — loads defaults, then merges `local/config.py`
   - **Dict** values are merged (local keys add to / replace defaults)
   - **Scalar** values replace the default wholesale
3. `fomc_tracker/loader.py` — auto-imports `local/*.py` at startup for
   side-effect registrations (e.g. `@data_source` decorators)

### Extension hooks
- `local/config.py` — override thresholds, weights, FRED series, URLs, colours
- `local/sources.py` — register custom data sources via `@data_source`
- `local/classifier.py` — register custom LLM classifier via `@classifier_backend`
- `local/participants.py` — export `EXTRA_PARTICIPANTS` list to add roster entries
- `local/seed_data.py` — export `EXTRA_SEED_DATA` dict to add historical data
- `local/meetings.py` — export `EXTRA_MEETINGS` list to add meeting dates

### Fork workflow
```bash
git fetch upstream && git merge upstream/main   # no conflicts with local/
```
