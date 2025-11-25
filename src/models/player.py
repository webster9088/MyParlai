"""Player model for sports data."""

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class PlayerStats:
    """Statistical data for a player.

    Attributes:
        games_played: Total games played.
        starts: Total games started.
        minutes: Average minutes per game.
        custom_stats: Sport-specific statistics.
    """

    games_played: int = 0
    starts: int = 0
    minutes: float = 0.0
    custom_stats: Dict[str, float] = field(default_factory=dict)


@dataclass
class Player:
    """Represents a sports player.

    Attributes:
        id: Unique player identifier.
        name: Player's full name.
        team_id: ID of the player's team.
        position: Player's position.
        jersey_number: Player's jersey number.
        status: Player's current status (active, injured, etc.).
        stats: Player statistics.
        injury_info: Current injury information if applicable.
    """

    id: str
    name: str
    team_id: str
    position: str
    jersey_number: Optional[int] = None
    status: str = "active"
    stats: PlayerStats = field(default_factory=PlayerStats)
    injury_info: Optional[str] = None

    @property
    def is_active(self) -> bool:
        """Check if player is active and available."""
        return self.status.lower() == "active"

    @property
    def is_injured(self) -> bool:
        """Check if player is injured."""
        return self.status.lower() in ["injured", "out", "doubtful", "questionable"]

    def to_dict(self) -> Dict:
        """Convert player to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "team_id": self.team_id,
            "position": self.position,
            "jersey_number": self.jersey_number,
            "status": self.status,
            "is_active": self.is_active,
            "injury_info": self.injury_info,
        }
