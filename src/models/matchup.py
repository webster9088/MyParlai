"""Matchup model for sports data."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional

from src.models.team import Team
from src.models.weather import Weather
from src.models.injury import InjuryReport


@dataclass
class Odds:
    """Betting odds for a matchup.

    Attributes:
        spread: Point spread (positive = underdog).
        spread_odds: Odds for the spread bet.
        moneyline_home: Moneyline odds for home team.
        moneyline_away: Moneyline odds for away team.
        over_under: Total points over/under line.
        over_odds: Odds for the over bet.
        under_odds: Odds for the under bet.
    """

    spread: float = 0.0
    spread_odds: int = -110
    moneyline_home: int = -110
    moneyline_away: int = -110
    over_under: float = 0.0
    over_odds: int = -110
    under_odds: int = -110

    def get_implied_probability(self, odds: int) -> float:
        """Calculate implied probability from American odds.

        Args:
            odds: American odds (positive or negative).

        Returns:
            Implied probability as a decimal (0-1).
        """
        if odds > 0:
            return 100 / (odds + 100)
        else:
            return abs(odds) / (abs(odds) + 100)

    @property
    def home_win_probability(self) -> float:
        """Get implied probability of home team winning."""
        return self.get_implied_probability(self.moneyline_home)

    @property
    def away_win_probability(self) -> float:
        """Get implied probability of away team winning."""
        return self.get_implied_probability(self.moneyline_away)


@dataclass
class HeadToHead:
    """Head-to-head record between two teams.

    Attributes:
        home_wins: Home team wins in matchup history.
        away_wins: Away team wins in matchup history.
        ties: Ties in matchup history.
        last_meeting: Date of last meeting.
        last_winner: ID of last winner.
        avg_total_points: Average total points in recent meetings.
    """

    home_wins: int = 0
    away_wins: int = 0
    ties: int = 0
    last_meeting: Optional[datetime] = None
    last_winner: Optional[str] = None
    avg_total_points: float = 0.0

    @property
    def total_games(self) -> int:
        """Get total games played between teams."""
        return self.home_wins + self.away_wins + self.ties


@dataclass
class Matchup:
    """Represents a sports matchup/game.

    Attributes:
        id: Unique matchup identifier.
        sport: Sport type.
        home_team: Home team.
        away_team: Away team.
        game_time: Scheduled game time.
        venue: Venue name.
        is_neutral_site: Whether game is at a neutral site.
        weather: Weather conditions for the game.
        odds: Betting odds for the game.
        home_injuries: Injury report for home team.
        away_injuries: Injury report for away team.
        head_to_head: Historical head-to-head record.
        analysis_factors: Additional factors for analysis.
    """

    id: str
    sport: str
    home_team: Team
    away_team: Team
    game_time: datetime
    venue: str
    is_neutral_site: bool = False
    weather: Optional[Weather] = None
    odds: Odds = field(default_factory=Odds)
    home_injuries: Optional[InjuryReport] = None
    away_injuries: Optional[InjuryReport] = None
    head_to_head: HeadToHead = field(default_factory=HeadToHead)
    analysis_factors: Dict[str, float] = field(default_factory=dict)

    @property
    def home_advantage(self) -> float:
        """Calculate home field advantage factor.

        Returns:
            Float representing home advantage (0-1).
        """
        if self.is_neutral_site:
            return 0.0

        # Base home advantage
        base_advantage = 0.03

        # Adjust based on team records
        home_pct = self.home_team.stats.win_percentage
        away_pct = self.away_team.stats.win_percentage

        if home_pct > 0.5:
            base_advantage += 0.01
        if away_pct < 0.5:
            base_advantage += 0.01

        return min(base_advantage, 0.1)

    @property
    def injury_differential(self) -> float:
        """Calculate injury impact differential.

        Returns:
            Positive value favors home team, negative favors away.
        """
        home_impact = self.home_injuries.get_total_impact() if self.home_injuries else 0
        away_impact = self.away_injuries.get_total_impact() if self.away_injuries else 0
        return away_impact - home_impact

    def get_summary(self) -> str:
        """Get a summary of the matchup.

        Returns:
            Human-readable summary string.
        """
        home = self.home_team.full_name
        away = self.away_team.full_name
        time_str = self.game_time.strftime("%Y-%m-%d %H:%M")
        return f"{away} @ {home} - {time_str} at {self.venue}"

    def to_dict(self) -> Dict:
        """Convert matchup to dictionary representation."""
        return {
            "id": self.id,
            "sport": self.sport,
            "home_team": self.home_team.to_dict(),
            "away_team": self.away_team.to_dict(),
            "game_time": self.game_time.isoformat(),
            "venue": self.venue,
            "is_neutral_site": self.is_neutral_site,
            "odds": {
                "spread": self.odds.spread,
                "moneyline_home": self.odds.moneyline_home,
                "moneyline_away": self.odds.moneyline_away,
                "over_under": self.odds.over_under,
            },
            "weather": self.weather.to_dict() if self.weather else None,
            "home_injuries": self.home_injuries.to_dict() if self.home_injuries else None,
            "away_injuries": self.away_injuries.to_dict() if self.away_injuries else None,
            "head_to_head": {
                "home_wins": self.head_to_head.home_wins,
                "away_wins": self.head_to_head.away_wins,
                "total_games": self.head_to_head.total_games,
            },
        }
