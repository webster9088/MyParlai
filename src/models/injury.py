"""Injury report model for sports data."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class InjuryStatus(Enum):
    """Player injury status levels."""

    OUT = "out"
    DOUBTFUL = "doubtful"
    QUESTIONABLE = "questionable"
    PROBABLE = "probable"
    DAY_TO_DAY = "day-to-day"
    IR = "injured_reserve"


@dataclass
class Injury:
    """Individual injury record.

    Attributes:
        player_id: ID of the injured player.
        player_name: Name of the injured player.
        team_id: ID of the player's team.
        status: Injury status.
        injury_type: Type of injury (e.g., "knee", "hamstring").
        description: Detailed description of the injury.
        estimated_return: Estimated return date if known.
        impact_score: Impact of this player's absence (0-1).
        updated_at: When the injury report was last updated.
    """

    player_id: str
    player_name: str
    team_id: str
    status: InjuryStatus
    injury_type: str
    description: Optional[str] = None
    estimated_return: Optional[datetime] = None
    impact_score: float = 0.5
    updated_at: datetime = None

    def __post_init__(self):
        """Initialize updated_at if not provided."""
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()

    @property
    def is_likely_out(self) -> bool:
        """Check if player is likely to miss the game."""
        return self.status in [InjuryStatus.OUT, InjuryStatus.DOUBTFUL, InjuryStatus.IR]

    @property
    def is_uncertain(self) -> bool:
        """Check if player's availability is uncertain."""
        return self.status in [InjuryStatus.QUESTIONABLE, InjuryStatus.DAY_TO_DAY]

    def to_dict(self) -> Dict:
        """Convert injury to dictionary representation."""
        return {
            "player_id": self.player_id,
            "player_name": self.player_name,
            "team_id": self.team_id,
            "status": self.status.value,
            "injury_type": self.injury_type,
            "description": self.description,
            "is_likely_out": self.is_likely_out,
            "impact_score": self.impact_score,
        }


@dataclass
class InjuryReport:
    """Injury report for a team.

    Attributes:
        team_id: ID of the team.
        team_name: Name of the team.
        injuries: List of injuries on the team.
        report_date: Date of the report.
    """

    team_id: str
    team_name: str
    injuries: List[Injury] = field(default_factory=list)
    report_date: datetime = None

    def __post_init__(self):
        """Initialize report_date if not provided."""
        if self.report_date is None:
            self.report_date = datetime.utcnow()

    @property
    def total_injuries(self) -> int:
        """Get total number of injuries."""
        return len(self.injuries)

    @property
    def players_out(self) -> List[Injury]:
        """Get list of players definitely out."""
        return [inj for inj in self.injuries if inj.is_likely_out]

    @property
    def players_questionable(self) -> List[Injury]:
        """Get list of questionable players."""
        return [inj for inj in self.injuries if inj.is_uncertain]

    def get_total_impact(self) -> float:
        """Calculate total impact of injuries.

        Returns:
            Sum of impact scores for all injuries (capped at 1.0).
        """
        total = sum(inj.impact_score for inj in self.injuries if inj.is_likely_out)
        total += sum(inj.impact_score * 0.5 for inj in self.injuries if inj.is_uncertain)
        return min(total, 1.0)

    def get_key_injuries(self, min_impact: float = 0.3) -> List[Injury]:
        """Get injuries with significant impact.

        Args:
            min_impact: Minimum impact score to consider.

        Returns:
            List of injuries with impact >= min_impact.
        """
        return [inj for inj in self.injuries if inj.impact_score >= min_impact]

    def to_dict(self) -> Dict:
        """Convert injury report to dictionary representation."""
        return {
            "team_id": self.team_id,
            "team_name": self.team_name,
            "total_injuries": self.total_injuries,
            "players_out": len(self.players_out),
            "players_questionable": len(self.players_questionable),
            "total_impact": self.get_total_impact(),
            "injuries": [inj.to_dict() for inj in self.injuries],
        }
