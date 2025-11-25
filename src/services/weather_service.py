"""Service for fetching weather data for game locations."""

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional

import requests

from src.models.weather import Weather, create_dome_weather


@dataclass
class WeatherAPIConfig:
    """Configuration for weather API.

    Attributes:
        base_url: Base URL for the weather API.
        api_key: API key for authentication.
        timeout: Request timeout in seconds.
    """

    base_url: str = "https://api.weatherapi.com/v1"
    api_key: Optional[str] = None
    timeout: int = 15

    @classmethod
    def from_env(cls) -> "WeatherAPIConfig":
        """Create config from environment variables."""
        return cls(
            base_url=os.getenv("WEATHER_API_BASE_URL", "https://api.weatherapi.com/v1"),
            api_key=os.getenv("WEATHER_API_KEY"),
            timeout=int(os.getenv("WEATHER_API_TIMEOUT", "15")),
        )


# Venues that are domes or indoor stadiums
DOME_VENUES = {
    # NFL
    "AT&T Stadium",
    "Allegiant Stadium",
    "Lucas Oil Stadium",
    "Mercedes-Benz Stadium",
    "U.S. Bank Stadium",
    "Caesars Superdome",
    "Ford Field",
    "State Farm Stadium",
    # NBA (all indoor)
    "all_nba",
    # NHL (all indoor)
    "all_nhl",
}


class WeatherService:
    """Service for fetching weather data.

    This service provides methods to retrieve weather conditions
    for game venues to factor into predictions.
    """

    def __init__(self, config: Optional[WeatherAPIConfig] = None):
        """Initialize the weather service.

        Args:
            config: API configuration. If None, loads from environment.
        """
        self.config = config or WeatherAPIConfig.from_env()
        self._session = None
        self._cache: Dict[str, tuple] = {}
        self._cache_ttl = 1800  # 30 minutes

    def _get_session(self) -> requests.Session:
        """Get or create a requests session."""
        if self._session is None:
            self._session = requests.Session()
        return self._session

    def _get_cached(self, key: str) -> Optional[Weather]:
        """Get cached weather if still valid."""
        if key in self._cache:
            data, timestamp = self._cache[key]
            if datetime.utcnow().timestamp() - timestamp < self._cache_ttl:
                return data
            del self._cache[key]
        return None

    def _set_cached(self, key: str, data: Weather) -> None:
        """Cache weather data with current timestamp."""
        self._cache[key] = (data, datetime.utcnow().timestamp())

    def is_dome_venue(self, venue: str, sport: str) -> bool:
        """Check if a venue is a dome or indoor stadium.

        Args:
            venue: Name of the venue.
            sport: Sport being played.

        Returns:
            True if the venue is indoor.
        """
        # NBA and NHL are always indoor
        if sport.upper() in ["NBA", "NHL"]:
            return True

        return venue in DOME_VENUES

    def get_weather(
        self,
        location: str,
        game_time: datetime,
        venue: str = "",
        sport: str = "NFL",
    ) -> Weather:
        """Get weather for a game location.

        Args:
            location: City or location for weather lookup.
            game_time: Time of the game.
            venue: Name of the venue.
            sport: Sport being played.

        Returns:
            Weather object with conditions.
        """
        # Check if indoor venue
        if self.is_dome_venue(venue, sport):
            return create_dome_weather()

        cache_key = f"weather_{location}_{game_time.strftime('%Y-%m-%d_%H')}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        # Return mock weather for demonstration
        weather = self._get_mock_weather(location, game_time)
        self._set_cached(cache_key, weather)
        return weather

    def get_weather_impact(
        self,
        weather: Weather,
        sport: str,
    ) -> Dict[str, float]:
        """Analyze weather impact on a specific sport.

        Args:
            weather: Weather conditions.
            sport: Sport being played.

        Returns:
            Dictionary of impact factors.
        """
        if weather.is_dome:
            return {
                "passing_impact": 0.0,
                "kicking_impact": 0.0,
                "scoring_impact": 0.0,
                "total_impact": 0.0,
            }

        impacts = {}

        # Calculate sport-specific impacts
        if sport.upper() in ["NFL", "NCAAF"]:
            # Wind affects passing and kicking
            passing_impact = min(weather.wind_speed / 40, 0.5)
            kicking_impact = min(weather.wind_speed / 25, 0.6)

            # Cold affects grip and performance
            if weather.temperature < 32:
                passing_impact += 0.1
                kicking_impact += 0.1

            # Rain/snow affects everything
            if weather.precipitation_chance > 50:
                passing_impact += 0.15
                kicking_impact += 0.2

            impacts = {
                "passing_impact": passing_impact,
                "kicking_impact": kicking_impact,
                "scoring_impact": (passing_impact + kicking_impact) / 2,
                "total_impact": weather.get_impact_score(),
            }

        elif sport.upper() in ["MLB"]:
            # Wind affects fly balls
            wind_impact = min(weather.wind_speed / 30, 0.4)

            # Temperature affects ball carry
            temp_impact = 0.0
            if weather.temperature < 50:
                temp_impact = 0.1
            elif weather.temperature > 85:
                temp_impact = -0.1  # Ball carries better

            impacts = {
                "hitting_impact": wind_impact,
                "pitching_impact": temp_impact,
                "scoring_impact": wind_impact + temp_impact,
                "total_impact": weather.get_impact_score(),
            }

        else:
            impacts = {
                "scoring_impact": weather.get_impact_score(),
                "total_impact": weather.get_impact_score(),
            }

        return impacts

    def _get_mock_weather(self, location: str, game_time: datetime) -> Weather:
        """Generate mock weather data for demonstration."""
        # Vary weather based on location
        location_lower = location.lower()

        if "miami" in location_lower or "phoenix" in location_lower:
            return Weather(
                temperature=82.0,
                feels_like=85.0,
                humidity=65.0,
                wind_speed=8.0,
                wind_direction="SE",
                precipitation_chance=20.0,
                conditions="Partly Cloudy",
            )
        elif "green bay" in location_lower or "buffalo" in location_lower:
            return Weather(
                temperature=28.0,
                feels_like=18.0,
                humidity=45.0,
                wind_speed=15.0,
                wind_direction="NW",
                precipitation_chance=30.0,
                conditions="Cold and Windy",
            )
        elif "seattle" in location_lower or "san francisco" in location_lower:
            return Weather(
                temperature=55.0,
                feels_like=52.0,
                humidity=75.0,
                wind_speed=12.0,
                wind_direction="W",
                precipitation_chance=45.0,
                conditions="Cloudy",
            )
        else:
            # Default moderate weather
            return Weather(
                temperature=65.0,
                feels_like=63.0,
                humidity=55.0,
                wind_speed=10.0,
                wind_direction="SW",
                precipitation_chance=15.0,
                conditions="Clear",
            )

    def close(self) -> None:
        """Close the HTTP session."""
        if self._session:
            self._session.close()
            self._session = None
