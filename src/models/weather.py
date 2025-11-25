"""Weather model for sports data."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Weather:
    """Weather conditions for a game.

    Attributes:
        temperature: Temperature in Fahrenheit.
        feels_like: Feels-like temperature in Fahrenheit.
        humidity: Humidity percentage.
        wind_speed: Wind speed in MPH.
        wind_direction: Wind direction (e.g., "NW").
        precipitation_chance: Chance of precipitation (0-100).
        conditions: Weather conditions description.
        visibility: Visibility in miles.
        is_dome: Whether the game is in a dome/indoor stadium.
        timestamp: When the weather data was fetched.
    """

    temperature: float
    feels_like: float
    humidity: float
    wind_speed: float
    wind_direction: str
    precipitation_chance: float
    conditions: str
    visibility: float = 10.0
    is_dome: bool = False
    timestamp: datetime = None

    def __post_init__(self):
        """Initialize timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    @property
    def is_severe(self) -> bool:
        """Check if weather conditions are severe."""
        if self.is_dome:
            return False
        return (
            self.wind_speed > 25
            or self.temperature < 20
            or self.temperature > 100
            or self.precipitation_chance > 70
        )

    @property
    def affects_gameplay(self) -> bool:
        """Check if weather significantly affects gameplay."""
        if self.is_dome:
            return False
        return (
            self.wind_speed > 15
            or self.temperature < 32
            or self.temperature > 90
            or self.precipitation_chance > 50
        )

    def get_impact_score(self) -> float:
        """Calculate weather impact score (0-1, higher = more impact).

        Returns:
            Float between 0 and 1 indicating weather impact.
        """
        if self.is_dome:
            return 0.0

        score = 0.0

        # Wind impact
        if self.wind_speed > 10:
            score += min((self.wind_speed - 10) / 30, 0.3)

        # Temperature impact
        if self.temperature < 32:
            score += min((32 - self.temperature) / 50, 0.25)
        elif self.temperature > 85:
            score += min((self.temperature - 85) / 30, 0.25)

        # Precipitation impact
        if self.precipitation_chance > 30:
            score += min((self.precipitation_chance - 30) / 100, 0.3)

        # Humidity impact
        if self.humidity > 70:
            score += min((self.humidity - 70) / 60, 0.15)

        return min(score, 1.0)

    def to_dict(self) -> dict:
        """Convert weather to dictionary representation."""
        return {
            "temperature": self.temperature,
            "feels_like": self.feels_like,
            "humidity": self.humidity,
            "wind_speed": self.wind_speed,
            "wind_direction": self.wind_direction,
            "precipitation_chance": self.precipitation_chance,
            "conditions": self.conditions,
            "visibility": self.visibility,
            "is_dome": self.is_dome,
            "is_severe": self.is_severe,
            "affects_gameplay": self.affects_gameplay,
            "impact_score": self.get_impact_score(),
        }


def create_dome_weather() -> Weather:
    """Create weather object for dome/indoor games.

    Returns:
        Weather object with neutral indoor conditions.
    """
    return Weather(
        temperature=72.0,
        feels_like=72.0,
        humidity=50.0,
        wind_speed=0.0,
        wind_direction="N/A",
        precipitation_chance=0.0,
        conditions="Indoor",
        is_dome=True,
    )
