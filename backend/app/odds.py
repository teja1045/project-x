from __future__ import annotations

import random
from typing import Literal

Sport = Literal["football", "cricket"]


class LicensedOddsFeed:
    """Simulated licensed odds feed adapter.

    Replace this class with an integration to a licensed odds API provider
    (for example an aggregator that may include Parimatch markets).
    """

    provider_name = "licensed-aggregator-sim"

    def get_live_market(self, sport: Sport, match_id: str) -> dict:
        seed = sum(ord(c) for c in f"{sport}:{match_id}")
        random.seed(seed)

        if sport == "football":
            return {
                "sport": sport,
                "matchId": match_id,
                "provider": self.provider_name,
                "markets": {
                    "homeWin": round(random.uniform(1.8, 2.8), 2),
                    "draw": round(random.uniform(2.8, 3.8), 2),
                    "awayWin": round(random.uniform(2.0, 3.2), 2),
                },
            }

        return {
            "sport": sport,
            "matchId": match_id,
            "provider": self.provider_name,
            "markets": {
                "homeWin": round(random.uniform(1.6, 2.4), 2),
                "awayWin": round(random.uniform(1.7, 2.5), 2),
            },
        }
