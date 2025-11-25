"""Parlay model for betting selections."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class BetType(Enum):
    """Types of bets that can be included in a parlay."""

    SPREAD = "spread"
    MONEYLINE = "moneyline"
    OVER = "over"
    UNDER = "under"
    PROP = "prop"


class PickConfidence(Enum):
    """Confidence levels for picks."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class ParlayLeg:
    """A single leg/pick in a parlay.

    Attributes:
        matchup_id: ID of the matchup for this pick.
        team_id: ID of the team picked (if applicable).
        bet_type: Type of bet.
        pick: The actual pick (e.g., "KC -3.5", "OVER 48.5").
        odds: Odds for this leg.
        confidence: Confidence level for this pick.
        confidence_score: Numerical confidence score (0-1).
        reasoning: AI reasoning for this pick.
        key_factors: Key factors that influenced the pick.
    """

    matchup_id: str
    bet_type: BetType
    pick: str
    odds: int = -110
    team_id: Optional[str] = None
    confidence: PickConfidence = PickConfidence.MEDIUM
    confidence_score: float = 0.5
    reasoning: str = ""
    key_factors: List[str] = field(default_factory=list)

    @property
    def implied_probability(self) -> float:
        """Calculate implied probability from odds.

        Returns:
            Implied probability as a decimal (0-1).
        """
        if self.odds > 0:
            return 100 / (self.odds + 100)
        else:
            return abs(self.odds) / (abs(self.odds) + 100)

    @property
    def decimal_odds(self) -> float:
        """Convert American odds to decimal odds.

        Returns:
            Decimal odds representation.
        """
        if self.odds > 0:
            return (self.odds / 100) + 1
        else:
            return (100 / abs(self.odds)) + 1

    def to_dict(self) -> Dict:
        """Convert parlay leg to dictionary representation."""
        return {
            "matchup_id": self.matchup_id,
            "team_id": self.team_id,
            "bet_type": self.bet_type.value,
            "pick": self.pick,
            "odds": self.odds,
            "implied_probability": self.implied_probability,
            "confidence": self.confidence.value,
            "confidence_score": self.confidence_score,
            "reasoning": self.reasoning,
            "key_factors": self.key_factors,
        }


@dataclass
class Parlay:
    """A complete parlay bet.

    Attributes:
        id: Unique parlay identifier.
        legs: List of parlay legs.
        stake: Amount to wager.
        created_at: When the parlay was created.
        sport: Sport for this parlay (or "mixed" for multi-sport).
        name: Optional name for the parlay.
    """

    id: str
    legs: List[ParlayLeg]
    stake: float = 10.0
    created_at: datetime = None
    sport: str = "mixed"
    name: Optional[str] = None

    def __post_init__(self):
        """Initialize created_at if not provided."""
        if self.created_at is None:
            self.created_at = datetime.utcnow()

    @property
    def num_legs(self) -> int:
        """Get number of legs in the parlay."""
        return len(self.legs)

    @property
    def total_odds(self) -> float:
        """Calculate total decimal odds for the parlay.

        Returns:
            Combined decimal odds.
        """
        if not self.legs:
            return 1.0
        total = 1.0
        for leg in self.legs:
            total *= leg.decimal_odds
        return total

    @property
    def potential_payout(self) -> float:
        """Calculate potential payout.

        Returns:
            Potential payout including stake.
        """
        return self.stake * self.total_odds

    @property
    def potential_profit(self) -> float:
        """Calculate potential profit.

        Returns:
            Potential profit (payout - stake).
        """
        return self.potential_payout - self.stake

    @property
    def average_confidence(self) -> float:
        """Calculate average confidence score across all legs.

        Returns:
            Average confidence score (0-1).
        """
        if not self.legs:
            return 0.0
        return sum(leg.confidence_score for leg in self.legs) / len(self.legs)

    @property
    def implied_win_probability(self) -> float:
        """Calculate implied probability of winning the parlay.

        Returns:
            Implied probability as a decimal (0-1).
        """
        if not self.legs:
            return 0.0
        prob = 1.0
        for leg in self.legs:
            prob *= leg.confidence_score
        return prob

    def get_american_odds(self) -> int:
        """Get total odds in American format.

        Returns:
            American odds representation.
        """
        decimal = self.total_odds
        if decimal >= 2.0:
            return int((decimal - 1) * 100)
        elif decimal > 1.0:
            return int(-100 / (decimal - 1))
        else:
            # Edge case: decimal == 1.0 (no legs or all even bets)
            return 0

    def get_summary(self) -> str:
        """Get a summary of the parlay.

        Returns:
            Human-readable summary string.
        """
        lines = [f"🎰 {self.name or 'Parlay'} ({self.num_legs} legs)"]
        lines.append(f"   Stake: ${self.stake:.2f}")
        lines.append(f"   Odds: {self.get_american_odds():+d}")
        lines.append(f"   Potential Payout: ${self.potential_payout:.2f}")
        lines.append(f"   Avg Confidence: {self.average_confidence:.1%}")
        lines.append("\n   Legs:")
        for i, leg in enumerate(self.legs, 1):
            if leg.confidence_score >= 0.6:
                conf_emoji = "🟢"
            elif leg.confidence_score >= 0.4:
                conf_emoji = "🟡"
            else:
                conf_emoji = "🔴"
            leg_line = f"   {i}. {conf_emoji} {leg.pick} ({leg.odds:+d}) - {leg.confidence.value}"
            lines.append(leg_line)
        return "\n".join(lines)

    def to_dict(self) -> Dict:
        """Convert parlay to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "sport": self.sport,
            "num_legs": self.num_legs,
            "stake": self.stake,
            "total_odds": self.total_odds,
            "american_odds": self.get_american_odds(),
            "potential_payout": self.potential_payout,
            "potential_profit": self.potential_profit,
            "average_confidence": self.average_confidence,
            "implied_win_probability": self.implied_win_probability,
            "created_at": self.created_at.isoformat(),
            "legs": [leg.to_dict() for leg in self.legs],
        }
