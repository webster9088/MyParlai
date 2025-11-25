"""Service for fetching betting odds data."""

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

from src.models.matchup import Odds


@dataclass
class OddsAPIConfig:
    """Configuration for odds API.

    Attributes:
        base_url: Base URL for the odds API.
        api_key: API key for authentication.
        timeout: Request timeout in seconds.
    """

    base_url: str = "https://api.the-odds-api.com/v4"
    api_key: Optional[str] = None
    timeout: int = 15

    @classmethod
    def from_env(cls) -> "OddsAPIConfig":
        """Create config from environment variables."""
        return cls(
            base_url=os.getenv("ODDS_API_BASE_URL", "https://api.the-odds-api.com/v4"),
            api_key=os.getenv("ODDS_API_KEY"),
            timeout=int(os.getenv("ODDS_API_TIMEOUT", "15")),
        )


# Sport key mappings for the odds API
SPORT_KEYS = {
    "NFL": "americanfootball_nfl",
    "NBA": "basketball_nba",
    "MLB": "baseball_mlb",
    "NHL": "icehockey_nhl",
    "NCAAF": "americanfootball_ncaaf",
    "NCAAB": "basketball_ncaab",
}


class OddsService:
    """Service for fetching betting odds.

    This service provides methods to retrieve current betting lines
    and odds from various sportsbooks.
    """

    def __init__(self, config: Optional[OddsAPIConfig] = None):
        """Initialize the odds service.

        Args:
            config: API configuration. If None, loads from environment.
        """
        self.config = config or OddsAPIConfig.from_env()
        self._session = None
        self._cache: Dict[str, tuple] = {}
        self._cache_ttl = 300  # 5 minutes for odds

    def _get_session(self) -> requests.Session:
        """Get or create a requests session."""
        if self._session is None:
            self._session = requests.Session()
        return self._session

    def _get_cached(self, key: str) -> Optional[Any]:
        """Get cached data if still valid."""
        if key in self._cache:
            data, timestamp = self._cache[key]
            if datetime.utcnow().timestamp() - timestamp < self._cache_ttl:
                return data
            del self._cache[key]
        return None

    def _set_cached(self, key: str, data: Any) -> None:
        """Cache data with current timestamp."""
        self._cache[key] = (data, datetime.utcnow().timestamp())

    def get_odds(self, sport: str, matchup_id: Optional[str] = None) -> List[Dict]:
        """Get betting odds for a sport.

        Args:
            sport: Sport identifier (e.g., "NFL", "NBA").
            matchup_id: Optional specific matchup to get odds for.

        Returns:
            List of odds data dictionaries.
        """
        cache_key = f"odds_{sport}_{matchup_id or 'all'}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        # Return mock data for demonstration
        odds_data = self._get_mock_odds(sport, matchup_id)
        self._set_cached(cache_key, odds_data)
        return odds_data

    def get_matchup_odds(
        self,
        sport: str,
        home_team: str,
        away_team: str,
    ) -> Odds:
        """Get odds for a specific matchup.

        Args:
            sport: Sport identifier.
            home_team: Home team name or abbreviation.
            away_team: Away team name or abbreviation.

        Returns:
            Odds object for the matchup.
        """
        all_odds = self.get_odds(sport)

        for odds_data in all_odds:
            if (
                home_team.lower() in odds_data.get("home_team", "").lower()
                or away_team.lower() in odds_data.get("away_team", "").lower()
            ):
                return Odds(
                    spread=odds_data.get("spread", 0.0),
                    spread_odds=odds_data.get("spread_odds", -110),
                    moneyline_home=odds_data.get("moneyline_home", -110),
                    moneyline_away=odds_data.get("moneyline_away", -110),
                    over_under=odds_data.get("over_under", 0.0),
                    over_odds=odds_data.get("over_odds", -110),
                    under_odds=odds_data.get("under_odds", -110),
                )

        # Return default odds if not found
        return Odds()

    def find_value_bets(
        self,
        sport: str,
        min_edge: float = 0.05,
    ) -> List[Dict]:
        """Find potential value bets based on line movements.

        Args:
            sport: Sport identifier.
            min_edge: Minimum edge required to flag a bet.

        Returns:
            List of potential value bets.
        """
        # This would analyze line movements and consensus data
        # For now, return mock data
        return []

    def get_consensus_pick(self, sport: str, matchup_id: str) -> Dict:
        """Get public betting consensus for a matchup.

        Args:
            sport: Sport identifier.
            matchup_id: Matchup identifier.

        Returns:
            Dictionary with consensus betting percentages.
        """
        # Mock consensus data
        return {
            "matchup_id": matchup_id,
            "spread_home_pct": 55,
            "spread_away_pct": 45,
            "ml_home_pct": 60,
            "ml_away_pct": 40,
            "over_pct": 52,
            "under_pct": 48,
        }

    def _get_mock_odds(self, sport: str, matchup_id: Optional[str]) -> List[Dict]:
        """Generate mock odds data for demonstration."""
        mock_matchups = {
            "NFL": [
                {
                    "home_team": "Kansas City Chiefs",
                    "away_team": "San Francisco 49ers",
                    "spread": -3.5,
                    "spread_odds": -110,
                    "moneyline_home": -175,
                    "moneyline_away": 155,
                    "over_under": 48.5,
                    "over_odds": -110,
                    "under_odds": -110,
                },
                {
                    "home_team": "Buffalo Bills",
                    "away_team": "Dallas Cowboys",
                    "spread": -2.5,
                    "spread_odds": -110,
                    "moneyline_home": -140,
                    "moneyline_away": 120,
                    "over_under": 52.5,
                    "over_odds": -105,
                    "under_odds": -115,
                },
            ],
            "NBA": [
                {
                    "home_team": "Boston Celtics",
                    "away_team": "Denver Nuggets",
                    "spread": -4.5,
                    "spread_odds": -110,
                    "moneyline_home": -180,
                    "moneyline_away": 160,
                    "over_under": 225.5,
                    "over_odds": -110,
                    "under_odds": -110,
                },
                {
                    "home_team": "Milwaukee Bucks",
                    "away_team": "Oklahoma City Thunder",
                    "spread": -2.0,
                    "spread_odds": -110,
                    "moneyline_home": -130,
                    "moneyline_away": 110,
                    "over_under": 230.5,
                    "over_odds": -108,
                    "under_odds": -112,
                },
            ],
        }

        return mock_matchups.get(sport.upper(), mock_matchups["NFL"])

    def close(self) -> None:
        """Close the HTTP session."""
        if self._session:
            self._session.close()
            self._session = None
