from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

HAS_FASTAPI = importlib.util.find_spec("fastapi") is not None

if HAS_FASTAPI:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)


@pytest.mark.skipif(not HAS_FASTAPI, reason="fastapi is not installed in this environment")
def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["mode"] == "analytics-only"
    assert payload["liveMatches"] >= 1


@pytest.mark.skipif(not HAS_FASTAPI, reason="fastapi is not installed in this environment")
def test_live_matches_contains_market_odds() -> None:
    response = client.get("/matches/live")
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert len(payload) >= 1
    assert "prediction" in payload[0]
    assert "marketOdds" in payload[0]


@pytest.mark.skipif(not HAS_FASTAPI, reason="fastapi is not installed in this environment")
def test_value_signal_endpoint() -> None:
    response = client.get("/signals/value/football/f001", params={"outcome": "homeWin"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["outcome"] == "homeWin"
    assert "edge" in payload
    assert "signal" in payload
