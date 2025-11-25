"""Team model for sports data."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class TeamStats:
    """Statistical data for a team.

    Attributes:
        wins: Total wins.
        losses: Total losses.
        ties: Total ties (if applicable).
        points_for: Total points scored.
        points_against: Total points allowed.
        home_record: Record at home (wins-losses).
        away_record: Record on the road (wins-losses).
        streak: Current win/loss streak (positive = wins).
        last_10: Record in last 10 games.
        custom_stats: Sport-specific statistics.
    """

    wins: int = 0
    losses: int = 0
    ties: int = 0
    points_for: int = 0
    points_against: int = 0
    home_record: str = "0-0"
    away_record: str = "0-0"
    streak: int = 0
    last_10: str = "0-0"
    custom_stats: Dict[str, float] = field(default_factory=dict)

    @property
    def win_percentage(self) -> float:
        """Calculate win percentage."""
        total = self.wins + self.losses + self.ties
        if total == 0:
            return 0.0
        return self.wins / total

    @property
    def point_differential(self) -> int:
        """Calculate point differential."""
        return self.points_for - self.points_against


@dataclass
class Team:
    """Represents a sports team.

    Attributes:
        id: Unique team identifier.
        name: Team name.
        abbreviation: Short team abbreviation.
        city: Team's city.
        sport: Sport the team plays.
        conference: Team's conference/division.
        stats: Team statistics.
        roster: List of player IDs on the team.
    """

    id: str
    name: str
    abbreviation: str
    city: str
    sport: str
    conference: Optional[str] = None
    division: Optional[str] = None
    stats: TeamStats = field(default_factory=TeamStats)
    roster: List[str] = field(default_factory=list)

    @property
    def full_name(self) -> str:
        """Get full team name with city."""
        return f"{self.city} {self.name}"

    def get_record(self) -> str:
        """Get team's record as a string."""
        if self.stats.ties > 0:
            return f"{self.stats.wins}-{self.stats.losses}-{self.stats.ties}"
        return f"{self.stats.wins}-{self.stats.losses}"

    def to_dict(self) -> Dict:
        """Convert team to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "abbreviation": self.abbreviation,
            "city": self.city,
            "full_name": self.full_name,
            "sport": self.sport,
            "conference": self.conference,
            "division": self.division,
            "record": self.get_record(),
            "win_percentage": self.stats.win_percentage,
        }
