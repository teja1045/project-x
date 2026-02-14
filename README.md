# Real-Time Cricket + Football Prediction + Odds Analytics Starter

This project is a **real-time analytics dashboard** (not a real-money betting platform).
It demonstrates how to combine:

- live match state updates,
- model probabilities,
- Parimatch-style market odds from a **licensed feed adapter**, and
- value-signal analytics.

## Why this approach

Direct scraping of bookmaker websites is risky and may violate terms. This starter is built around a pluggable `LicensedOddsFeed` adapter so you can integrate a legal/provider-approved odds API.

## Features

- Real-time in-memory live simulation for football + cricket.
- Prediction engine outputs probabilities + fair odds.
- Simulated licensed odds feed adapter (`backend/app/odds.py`) to swap with a real provider.
- Value signal endpoint compares model probability vs market implied probability.
- WebSocket stream with prediction + market odds updates every second.
- Simple web dashboard at `/`.

## API

- `GET /matches/live` – list live matches with model predictions and market odds.
- `GET /predict/{sport}/{match_id}` – enriched prediction + market odds.
- `GET /signals/value/{sport}/{match_id}?outcome=homeWin` – value signal for selected outcome.
- `WS /ws/live/{sport}/{match_id}` – streaming payload with prediction + market odds.

## Run

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open:
- Dashboard: `http://127.0.0.1:8000/`
- API docs: `http://127.0.0.1:8000/docs`

## Swap in a real odds provider

1. Replace `LicensedOddsFeed.get_live_market(...)` in `backend/app/odds.py` with your provider's SDK/HTTP calls.
2. Normalize provider response to this shape:
   - `{"markets": {"homeWin": <odds>, "draw": <odds>, "awayWin": <odds>}}` for football
   - `{"markets": {"homeWin": <odds>, "awayWin": <odds>}}` for cricket
3. Keep provider credentials in environment variables.

## Important note

This repository is for analytics/product prototyping only. If you later add wagering or money movement, implement authentication, KYC/AML, audit logs, payment compliance, and local legal review first.
