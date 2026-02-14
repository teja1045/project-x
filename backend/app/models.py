from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Sport = Literal["football", "cricket"]


@dataclass
class TeamSnapshot:
    name: str
    recent_form: float
    attack_strength: float
    defense_strength: float


@dataclass
class MatchContext:
    match_id: str
    minute_or_over: float
    home_score: int
    away_score: int
    home: TeamSnapshot
    away: TeamSnapshot


class PredictionEngine:
    """Deterministic baseline that outputs probability, score projection, and fair odds."""

    @staticmethod
    def _bounded(value: float, lower: float = 0.01, upper: float = 0.99) -> float:
        return max(lower, min(upper, value))

    @staticmethod
    def _fair_odds(probability: float) -> float:
        return round(1 / max(probability, 0.01), 2)

    def _momentum(self, context: MatchContext) -> float:
        form_delta = context.home.recent_form - context.away.recent_form
        attack_delta = context.home.attack_strength - context.away.attack_strength
        defense_delta = context.away.defense_strength - context.home.defense_strength
        score_delta = context.home_score - context.away_score
        return (form_delta * 0.30) + (attack_delta * 0.35) + (defense_delta * 0.20) + (score_delta * 0.15)

    def predict_outcome(self, sport: Sport, context: MatchContext) -> dict:
        momentum = self._momentum(context)

        if sport == "football":
            home_win = self._bounded(0.44 + momentum * 0.28)
            away_win = self._bounded(0.30 - momentum * 0.24)
            draw = self._bounded(1.0 - home_win - away_win)
            total = home_win + away_win + draw

            home_win /= total
            away_win /= total
            draw /= total

            return {
                "sport": sport,
                "matchId": context.match_id,
                "minute": context.minute_or_over,
                "score": {"home": context.home_score, "away": context.away_score},
                "probabilities": {
                    "homeWin": round(home_win, 4),
                    "draw": round(draw, 4),
                    "awayWin": round(away_win, 4),
                },
                "fairOdds": {
                    "homeWin": self._fair_odds(home_win),
                    "draw": self._fair_odds(draw),
                    "awayWin": self._fair_odds(away_win),
                },
                "expectedGoals": {
                    "home": round(0.6 + context.home.attack_strength * 1.6, 2),
                    "away": round(0.5 + context.away.attack_strength * 1.4, 2),
                },
            }

        home_win = self._bounded(0.48 + momentum * 0.33)
        away_win = self._bounded(1.0 - home_win)
        return {
            "sport": sport,
            "matchId": context.match_id,
            "over": context.minute_or_over,
            "score": {"home": context.home_score, "away": context.away_score},
            "probabilities": {
                "homeWin": round(home_win, 4),
                "awayWin": round(away_win, 4),
            },
            "fairOdds": {
                "homeWin": self._fair_odds(home_win),
                "awayWin": self._fair_odds(away_win),
            },
            "projectedRuns": {
                "home": round(
                    context.home_score + (20 - min(context.minute_or_over, 20)) * (6 + context.home.attack_strength * 2)
                ),
                "away": round(
                    context.away_score + (20 - min(context.minute_or_over, 20)) * (6 + context.away.attack_strength * 2)
                ),
            },
        }


def value_signal(model_probability: float, market_odds: float) -> dict:
    """Analytics-only signal comparing model probability versus market implied probability."""

    implied_probability = 1 / market_odds
    edge = model_probability - implied_probability
    if edge <= 0:
        return {
            "edge": round(edge, 4),
            "signal": "No value",
            "confidence": "low",
        }

    confidence = "medium" if edge < 0.07 else "high"
    return {
        "edge": round(edge, 4),
        "signal": "Potential value",
        "confidence": confidence,
    }
