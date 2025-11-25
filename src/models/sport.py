"""Sport enumeration and configuration."""

from dataclasses import dataclass
from enum import Enum
from typing import List


class SportType(Enum):
    """Supported sport types."""

    NFL = "nfl"
    NBA = "nba"
    MLB = "mlb"
    NHL = "nhl"
    NCAAF = "ncaaf"
    NCAAB = "ncaab"
    SOCCER = "soccer"


@dataclass
class Sport:
    """Sport configuration and metadata.

    Attributes:
        sport_type: The type of sport.
        name: Human-readable name of the sport.
        season_active: Whether the sport is currently in season.
        weather_affects: Whether weather significantly impacts the sport.
        factors: List of key factors to consider for analysis.
    """

    sport_type: SportType
    name: str
    season_active: bool = True
    weather_affects: bool = False
    factors: List[str] = None

    def __post_init__(self):
        """Initialize default factors based on sport type."""
        if self.factors is None:
            self.factors = self._get_default_factors()

    def _get_default_factors(self) -> List[str]:
        """Get default analysis factors for the sport."""
        base_factors = ["team_record", "head_to_head", "injuries", "home_away"]

        sport_specific = {
            SportType.NFL: ["weather", "bye_week", "travel_distance", "time_of_possession"],
            SportType.NBA: ["back_to_back", "rest_days", "pace", "three_point_shooting"],
            SportType.MLB: ["pitcher_matchup", "bullpen_usage", "weather", "park_factors"],
            SportType.NHL: ["goalie_matchup", "power_play", "penalty_kill", "shots_on_goal"],
            SportType.NCAAF: ["weather", "conference_play", "rivalry", "strength_of_schedule"],
            SportType.NCAAB: ["conference_play", "tempo", "turnovers", "rebounding"],
            SportType.SOCCER: ["home_advantage", "rest_days", "travel", "recent_form"],
        }

        return base_factors + sport_specific.get(self.sport_type, [])

    @classmethod
    def from_string(cls, sport_name: str) -> "Sport":
        """Create a Sport instance from a string name.

        Args:
            sport_name: Name of the sport (case-insensitive).

        Returns:
            Sport instance for the specified sport.

        Raises:
            ValueError: If the sport name is not recognized.
        """
        sport_map = {
            "nfl": (SportType.NFL, "National Football League", True),
            "nba": (SportType.NBA, "National Basketball Association", False),
            "mlb": (SportType.MLB, "Major League Baseball", True),
            "nhl": (SportType.NHL, "National Hockey League", False),
            "ncaaf": (SportType.NCAAF, "NCAA Football", True),
            "ncaab": (SportType.NCAAB, "NCAA Basketball", False),
            "soccer": (SportType.SOCCER, "Soccer", True),
        }

        key = sport_name.lower()
        if key not in sport_map:
            valid_sports = ", ".join(sport_map.keys())
            raise ValueError(f"Unknown sport: {sport_name}. Valid options: {valid_sports}")

        sport_type, name, weather_affects = sport_map[key]
        return cls(sport_type=sport_type, name=name, weather_affects=weather_affects)
