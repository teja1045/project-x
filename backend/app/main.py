from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query, WebSocket
from fastapi.responses import FileResponse

from .models import MatchContext, PredictionEngine, TeamSnapshot, value_signal
from .odds import LicensedOddsFeed

app = FastAPI(title="Sports Prediction + Odds Analytics API", version="0.4.0")
engine = PredictionEngine()
odds_feed = LicensedOddsFeed()

Sport = Literal["football", "cricket"]


@dataclass
class LiveMatch:
    sport: Sport
    match_id: str
    minute_or_over: float
    home_score: int
    away_score: int
    home: TeamSnapshot
    away: TeamSnapshot


LIVE_MATCHES: dict[str, LiveMatch] = {
    "football:f001": LiveMatch(
        sport="football",
        match_id="f001",
        minute_or_over=0,
        home_score=0,
        away_score=0,
        home=TeamSnapshot("Falcons", 0.65, 0.72, 0.66),
        away=TeamSnapshot("Tigers", 0.57, 0.64, 0.61),
    ),
    "cricket:c001": LiveMatch(
        sport="cricket",
        match_id="c001",
        minute_or_over=0,
        home_score=0,
        away_score=0,
        home=TeamSnapshot("Royals", 0.61, 0.69, 0.58),
        away=TeamSnapshot("Warriors", 0.59, 0.66, 0.6),
    ),
}


def _ctx(match: LiveMatch) -> MatchContext:
    return MatchContext(
        match_id=match.match_id,
        minute_or_over=match.minute_or_over,
        home_score=match.home_score,
        away_score=match.away_score,
        home=match.home,
        away=match.away,
    )


def _key(sport: Sport, match_id: str) -> str:
    return f"{sport}:{match_id}"


async def live_simulator() -> None:
    while True:
        for match in LIVE_MATCHES.values():
            if match.sport == "football":
                if match.minute_or_over < 90:
                    match.minute_or_over += 1
                    if random.random() < 0.04:
                        match.home_score += 1
                    if random.random() < 0.03:
                        match.away_score += 1
            else:
                if match.minute_or_over < 20:
                    match.minute_or_over = round(match.minute_or_over + 0.2, 1)
                    match.home_score += random.choice([0, 1, 2, 4, 6])
                    match.away_score += random.choice([0, 1, 2, 4, 6])
        await asyncio.sleep(1)


@app.on_event("startup")
async def startup() -> None:
    asyncio.create_task(live_simulator())


@app.get("/")
def index() -> FileResponse:
    return FileResponse(Path(__file__).parent / "static" / "index.html")


@app.get("/health")
def health() -> dict:
    return {
        "ok": True,
        "mode": "analytics-only",
        "liveMatches": len(LIVE_MATCHES),
        "oddsProvider": odds_feed.provider_name,
    }


@app.get("/matches/live")
def get_live_matches() -> list[dict]:
    payload = []
    for match in LIVE_MATCHES.values():
        prediction = engine.predict_outcome(match.sport, _ctx(match))
        market = odds_feed.get_live_market(match.sport, match.match_id)
        payload.append(
            {
                "sport": match.sport,
                "matchId": match.match_id,
                "teams": {"home": match.home.name, "away": match.away.name},
                "prediction": prediction,
                "marketOdds": market,
            }
        )
    return payload


@app.get("/predict/{sport}/{match_id}")
def predict_match(sport: Sport, match_id: str) -> dict:
    match = LIVE_MATCHES.get(_key(sport, match_id))
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    prediction = engine.predict_outcome(sport, _ctx(match))
    market = odds_feed.get_live_market(sport, match_id)
    return {"prediction": prediction, "marketOdds": market}


@app.get("/signals/value/{sport}/{match_id}")
def value_signals(sport: Sport, match_id: str, outcome: str = Query(..., description="Outcome key e.g. homeWin/draw/awayWin")) -> dict:
    match = LIVE_MATCHES.get(_key(sport, match_id))
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    prediction = engine.predict_outcome(sport, _ctx(match))
    probs = prediction["probabilities"]
    market = odds_feed.get_live_market(sport, match_id)["markets"]

    if outcome not in probs:
        raise HTTPException(status_code=400, detail=f"outcome must be one of: {', '.join(probs.keys())}")
    if outcome not in market:
        raise HTTPException(status_code=400, detail=f"market odds not available for outcome: {outcome}")

    signal = value_signal(model_probability=probs[outcome], market_odds=market[outcome])
    return {
        "sport": sport,
        "matchId": match_id,
        "outcome": outcome,
        "modelProbability": probs[outcome],
        "marketOdds": market[outcome],
        **signal,
    }


@app.websocket("/ws/live/{sport}/{match_id}")
async def stream_prediction(websocket: WebSocket, sport: Sport, match_id: str) -> None:
    match = LIVE_MATCHES.get(_key(sport, match_id))
    if not match:
        await websocket.close(code=4404)
        return

    await websocket.accept()
    while True:
        prediction = engine.predict_outcome(sport, _ctx(match))
        market = odds_feed.get_live_market(sport, match_id)
        await websocket.send_json({"prediction": prediction, "marketOdds": market})
        await asyncio.sleep(1)
