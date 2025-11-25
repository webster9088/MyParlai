"""
Sports Data API Client for fetching live sports odds and game data.

This module provides functionality to fetch live sports data from The Odds API.

Required API Keys:
    ODDS_API_KEY: API key from The Odds API (https://the-odds-api.com/)
                  Free tier provides 500 requests per month.
"""
import os
from typing import Optional
import requests
from dotenv import load_dotenv


load_dotenv()

# The Odds API base URL
BASE_URL = "https://api.the-odds-api.com/v4"

# Default request timeout in seconds
DEFAULT_TIMEOUT = 30

# Environment variable name for the API key
ODDS_API_KEY_ENV = "ODDS_API_KEY"


class APIKeyMissingError(Exception):
    """Exception raised when a required API key is missing."""

    pass


class SportsDataClient:
    """Client for fetching live sports data from The Odds API."""

    def __init__(self, api_key: Optional[str] = None, timeout: int = DEFAULT_TIMEOUT):
        """
        Initialize the sports data client.

        Args:
            api_key: Optional API key. If not provided, will try to load from
                     environment variable ODDS_API_KEY.
            timeout: Request timeout in seconds (default: 30).

        Note:
            To get an API key, visit https://the-odds-api.com/ and sign up
            for a free account. The free tier provides 500 requests per month.
        """
        self.api_key = api_key or os.getenv(ODDS_API_KEY_ENV, "")
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.timeout = timeout

    def has_api_key(self) -> bool:
        """
        Check if an API key is configured.

        Returns:
            True if API key is set, False otherwise.
        """
        return bool(self.api_key)

    def validate_api_key(self) -> None:
        """
        Validate that an API key is configured.

        Raises:
            APIKeyMissingError: If no API key is configured.
        """
        if not self.has_api_key():
            raise APIKeyMissingError(
                f"No API key configured. Set the {ODDS_API_KEY_ENV} environment "
                "variable or pass api_key to the constructor. "
                "Get your free API key at: https://the-odds-api.com/"
            )

    def get_sports(self) -> list:
        """
        Get list of available sports.

        Returns:
            List of available sports with their keys and titles.

        Raises:
            APIKeyMissingError: If no API key is configured.
        """
        self.validate_api_key()
        url = f"{self.base_url}/sports"
        params = {"apiKey": self.api_key}

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching sports: {e}")
            return []

    def get_odds(
        self,
        sport: str = "upcoming",
        regions: str = "us",
        markets: str = "h2h,spreads,totals",
        odds_format: str = "american",
    ) -> list:
        """
        Get odds for a specific sport.

        Args:
            sport: Sport key (e.g., 'americanfootball_nfl', 'basketball_nba')
                   Use 'upcoming' for all upcoming games across sports.
            regions: Comma-separated list of regions for bookmaker data
                     (us, us2, uk, eu, au)
            markets: Comma-separated list of markets (h2h, spreads, totals)
            odds_format: Format for odds (american, decimal, fractional)

        Returns:
            List of games with odds from various bookmakers.

        Raises:
            APIKeyMissingError: If no API key is configured.
        """
        self.validate_api_key()
        url = f"{self.base_url}/sports/{sport}/odds"
        params = {
            "apiKey": self.api_key,
            "regions": regions,
            "markets": markets,
            "oddsFormat": odds_format,
        }

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching odds: {e}")
            return []

    def get_scores(
        self, sport: str, days_from: int = 1, date_format: str = "iso"
    ) -> list:
        """
        Get live and recent scores for a sport.

        Args:
            sport: Sport key (e.g., 'americanfootball_nfl')
            days_from: Number of days in the past to return completed games
            date_format: Format for dates (iso or unix)

        Returns:
            List of games with scores.

        Raises:
            APIKeyMissingError: If no API key is configured.
        """
        self.validate_api_key()
        url = f"{self.base_url}/sports/{sport}/scores"
        params = {
            "apiKey": self.api_key,
            "daysFrom": days_from,
            "dateFormat": date_format,
        }

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching scores: {e}")
            return []


# Sample data for testing without API key
def get_sample_odds_data() -> list:
    """
    Get sample odds data for testing and demonstration purposes.

    Returns:
        List of sample games with odds.
    """
    return [
        {
            "id": "game1",
            "sport_key": "americanfootball_nfl",
            "sport_title": "NFL",
            "commence_time": "2024-01-15T18:00:00Z",
            "home_team": "Kansas City Chiefs",
            "away_team": "Buffalo Bills",
            "bookmakers": [
                {
                    "key": "draftkings",
                    "title": "DraftKings",
                    "markets": [
                        {
                            "key": "h2h",
                            "outcomes": [
                                {"name": "Kansas City Chiefs", "price": -150},
                                {"name": "Buffalo Bills", "price": 130},
                            ],
                        },
                        {
                            "key": "spreads",
                            "outcomes": [
                                {
                                    "name": "Kansas City Chiefs",
                                    "price": -110,
                                    "point": -3.0,
                                },
                                {
                                    "name": "Buffalo Bills",
                                    "price": -110,
                                    "point": 3.0,
                                },
                            ],
                        },
                    ],
                }
            ],
        },
        {
            "id": "game2",
            "sport_key": "basketball_nba",
            "sport_title": "NBA",
            "commence_time": "2024-01-15T19:30:00Z",
            "home_team": "Los Angeles Lakers",
            "away_team": "Boston Celtics",
            "bookmakers": [
                {
                    "key": "draftkings",
                    "title": "DraftKings",
                    "markets": [
                        {
                            "key": "h2h",
                            "outcomes": [
                                {"name": "Los Angeles Lakers", "price": 110},
                                {"name": "Boston Celtics", "price": -130},
                            ],
                        },
                        {
                            "key": "totals",
                            "outcomes": [
                                {"name": "Over", "price": -110, "point": 225.5},
                                {"name": "Under", "price": -110, "point": 225.5},
                            ],
                        },
                    ],
                }
            ],
        },
        {
            "id": "game3",
            "sport_key": "icehockey_nhl",
            "sport_title": "NHL",
            "commence_time": "2024-01-15T20:00:00Z",
            "home_team": "Vegas Golden Knights",
            "away_team": "Colorado Avalanche",
            "bookmakers": [
                {
                    "key": "fanduel",
                    "title": "FanDuel",
                    "markets": [
                        {
                            "key": "h2h",
                            "outcomes": [
                                {"name": "Vegas Golden Knights", "price": -120},
                                {"name": "Colorado Avalanche", "price": 100},
                            ],
                        }
                    ],
                }
            ],
        },
    ]


def get_sample_sports_data() -> list:
    """
    Get sample sports data for testing and demonstration purposes.

    Returns:
        List of sample available sports.
    """
    return [
        {
            "key": "americanfootball_nfl",
            "group": "American Football",
            "title": "NFL",
            "description": "US Football",
            "active": True,
        },
        {
            "key": "basketball_nba",
            "group": "Basketball",
            "title": "NBA",
            "description": "US Basketball",
            "active": True,
        },
        {
            "key": "icehockey_nhl",
            "group": "Ice Hockey",
            "title": "NHL",
            "description": "US Ice Hockey",
            "active": True,
        },
        {
            "key": "baseball_mlb",
            "group": "Baseball",
            "title": "MLB",
            "description": "Major League Baseball",
            "active": True,
        },
        {
            "key": "soccer_epl",
            "group": "Soccer",
            "title": "EPL",
            "description": "English Premier League",
            "active": True,
        },
    ]
