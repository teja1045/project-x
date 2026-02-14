from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.models import MatchContext, PredictionEngine, TeamSnapshot, value_signal
from app.odds import LicensedOddsFeed


def test_prediction_engine_football_probabilities_sum_to_one() -> None:
    engine = PredictionEngine()
    context = MatchContext(
        match_id="f001",
        minute_or_over=35,
        home_score=1,
        away_score=0,
        home=TeamSnapshot("Home", 0.62, 0.7, 0.66),
        away=TeamSnapshot("Away", 0.57, 0.64, 0.61),
    )

    payload = engine.predict_outcome("football", context)
    probs = payload["probabilities"]
    total = probs["homeWin"] + probs["draw"] + probs["awayWin"]
    assert abs(total - 1.0) < 0.001


def test_value_signal_schema() -> None:
    signal = value_signal(model_probability=0.55, market_odds=2.2)
    assert "edge" in signal
    assert signal["signal"] in {"No value", "Potential value"}


def test_licensed_odds_feed_market_keys() -> None:
    feed = LicensedOddsFeed()
    football = feed.get_live_market("football", "f001")
    cricket = feed.get_live_market("cricket", "c001")

    assert set(football["markets"].keys()) == {"homeWin", "draw", "awayWin"}
    assert set(cricket["markets"].keys()) == {"homeWin", "awayWin"}
