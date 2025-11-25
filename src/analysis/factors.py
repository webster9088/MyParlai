"""Factor analysis for sports predictions."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from src.models.matchup import Matchup


@dataclass
class Factor:
    """A single analysis factor.

    Attributes:
        name: Name of the factor.
        value: Numerical value (positive favors home, negative favors away).
        weight: Importance weight for this factor (0-1).
        description: Human-readable description.
    """

    name: str
    value: float
    weight: float = 0.1
    description: str = ""

    @property
    def weighted_value(self) -> float:
        """Get the weighted value of this factor."""
        return self.value * self.weight


@dataclass
class FactorAnalysis:
    """Complete factor analysis for a matchup.

    Attributes:
        matchup_id: ID of the analyzed matchup.
        factors: List of analyzed factors.
        home_score: Total score favoring home team.
        away_score: Total score favoring away team.
        predicted_winner: Predicted winner ID.
        confidence: Confidence in the prediction (0-1).
    """

    matchup_id: str
    factors: List[Factor] = field(default_factory=list)
    home_score: float = 0.0
    away_score: float = 0.0
    predicted_winner: Optional[str] = None
    confidence: float = 0.5

    def add_factor(self, factor: Factor) -> None:
        """Add a factor to the analysis."""
        self.factors.append(factor)
        if factor.weighted_value > 0:
            self.home_score += factor.weighted_value
        else:
            self.away_score += abs(factor.weighted_value)

    def calculate_prediction(self) -> None:
        """Calculate the predicted winner and confidence."""
        total = self.home_score + self.away_score
        if total == 0:
            self.confidence = 0.5
            return

        # Calculate base confidence as the proportion of the winning side
        # Then scale to be between 0.5 and 1.0 (since we're picking a winner)
        max_score = max(self.home_score, self.away_score)
        base_ratio = max_score / total  # This is 0.5-1.0
        # Scale to give meaningful confidence values
        self.confidence = 0.5 + (base_ratio - 0.5) * 0.8
        self.confidence = min(max(self.confidence, 0.5), 0.95)


class FactorAnalyzer:
    """Analyzes various factors that affect game outcomes.

    This class evaluates multiple factors including team performance,
    injuries, weather, and head-to-head records to make predictions.
    """

    # Factor weights by category
    DEFAULT_WEIGHTS = {
        "team_record": 0.20,
        "head_to_head": 0.10,
        "injuries": 0.15,
        "home_advantage": 0.10,
        "weather": 0.10,
        "recent_form": 0.15,
        "rest_days": 0.10,
        "matchup_specific": 0.10,
    }

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """Initialize the factor analyzer.

        Args:
            weights: Custom weights for factors. If None, uses defaults.
        """
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()

    def analyze(self, matchup: Matchup) -> FactorAnalysis:
        """Perform complete factor analysis on a matchup.

        Args:
            matchup: The matchup to analyze.

        Returns:
            FactorAnalysis with all evaluated factors.
        """
        analysis = FactorAnalysis(matchup_id=matchup.id)

        # Analyze each factor
        analysis.add_factor(self._analyze_team_records(matchup))
        analysis.add_factor(self._analyze_head_to_head(matchup))
        analysis.add_factor(self._analyze_injuries(matchup))
        analysis.add_factor(self._analyze_home_advantage(matchup))

        if matchup.weather:
            analysis.add_factor(self._analyze_weather(matchup))

        analysis.add_factor(self._analyze_recent_form(matchup))

        # Calculate final prediction
        analysis.calculate_prediction()

        # Set predicted winner
        if analysis.home_score > analysis.away_score:
            analysis.predicted_winner = matchup.home_team.id
        else:
            analysis.predicted_winner = matchup.away_team.id

        return analysis

    def _analyze_team_records(self, matchup: Matchup) -> Factor:
        """Analyze team win/loss records."""
        home_pct = matchup.home_team.stats.win_percentage
        away_pct = matchup.away_team.stats.win_percentage

        diff = home_pct - away_pct
        weight = self.weights["team_record"]

        if diff > 0.2:
            desc = (f"Home team ({home_pct:.1%}) significantly better "
                    f"record than away ({away_pct:.1%})")
        elif diff < -0.2:
            desc = (f"Away team ({away_pct:.1%}) significantly better "
                    f"record than home ({home_pct:.1%})")
        else:
            desc = f"Similar records: Home {home_pct:.1%} vs Away {away_pct:.1%}"

        return Factor(
            name="team_record",
            value=diff,
            weight=weight,
            description=desc,
        )

    def _analyze_head_to_head(self, matchup: Matchup) -> Factor:
        """Analyze head-to-head record between teams."""
        h2h = matchup.head_to_head
        total = h2h.total_games

        if total == 0:
            return Factor(
                name="head_to_head",
                value=0.0,
                weight=self.weights["head_to_head"],
                description="No head-to-head history",
            )

        home_win_pct = h2h.home_wins / total
        away_win_pct = h2h.away_wins / total
        diff = home_win_pct - away_win_pct

        return Factor(
            name="head_to_head",
            value=diff * 0.5,  # Scale down H2H importance
            weight=self.weights["head_to_head"],
            description=f"H2H record: Home {h2h.home_wins}-{h2h.away_wins} Away",
        )

    def _analyze_injuries(self, matchup: Matchup) -> Factor:
        """Analyze injury impact for both teams."""
        home_impact = 0.0
        away_impact = 0.0

        if matchup.home_injuries:
            home_impact = matchup.home_injuries.get_total_impact()

        if matchup.away_injuries:
            away_impact = matchup.away_injuries.get_total_impact()

        # Positive diff means away team has more injuries (favors home)
        diff = away_impact - home_impact

        if abs(diff) > 0.3:
            if diff > 0:
                desc = "Away team significantly more impacted by injuries"
            else:
                desc = "Home team significantly more impacted by injuries"
        else:
            desc = "Similar injury situations for both teams"

        return Factor(
            name="injuries",
            value=diff,
            weight=self.weights["injuries"],
            description=desc,
        )

    def _analyze_home_advantage(self, matchup: Matchup) -> Factor:
        """Analyze home field/court advantage."""
        if matchup.is_neutral_site:
            return Factor(
                name="home_advantage",
                value=0.0,
                weight=self.weights["home_advantage"],
                description="Neutral site - no home advantage",
            )

        # Base home advantage varies by sport
        sport_advantage = {
            "NFL": 0.08,
            "NBA": 0.06,
            "MLB": 0.04,
            "NHL": 0.05,
            "NCAAF": 0.10,
            "NCAAB": 0.08,
        }

        advantage = sport_advantage.get(matchup.sport.upper(), 0.05)

        return Factor(
            name="home_advantage",
            value=advantage,
            weight=self.weights["home_advantage"],
            description=f"Home field advantage for {matchup.home_team.full_name}",
        )

    def _analyze_weather(self, matchup: Matchup) -> Factor:
        """Analyze weather impact on the game."""
        weather = matchup.weather
        if not weather or weather.is_dome:
            return Factor(
                name="weather",
                value=0.0,
                weight=self.weights["weather"],
                description="Indoor game - no weather impact",
            )

        # Weather generally reduces scoring and increases variance
        # This is neutral between teams unless one is more suited to conditions
        desc = (f"Weather impact: {weather.conditions}, "
                f"{weather.temperature}°F, wind {weather.wind_speed}mph")

        return Factor(
            name="weather",
            value=0.0,  # Neutral for now, could be enhanced
            weight=self.weights["weather"],
            description=desc,
        )

    def _analyze_recent_form(self, matchup: Matchup) -> Factor:
        """Analyze recent performance/form."""
        home_streak = matchup.home_team.stats.streak
        away_streak = matchup.away_team.stats.streak

        # Convert streak to a form value (-1 to 1)
        home_form = min(max(home_streak / 5, -1), 1)
        away_form = min(max(away_streak / 5, -1), 1)

        diff = home_form - away_form

        if home_streak > 0:
            home_desc = f"Home on {home_streak}W streak"
        else:
            home_desc = f"Home on {abs(home_streak)}L streak"

        if away_streak > 0:
            away_desc = f"Away on {away_streak}W streak"
        else:
            away_desc = f"Away on {abs(away_streak)}L streak"

        return Factor(
            name="recent_form",
            value=diff * 0.5,
            weight=self.weights["recent_form"],
            description=f"{home_desc}, {away_desc}",
        )

    def get_key_factors(self, analysis: FactorAnalysis, top_n: int = 3) -> List[Factor]:
        """Get the most impactful factors from an analysis.

        Args:
            analysis: The factor analysis.
            top_n: Number of top factors to return.

        Returns:
            List of the most impactful factors.
        """
        sorted_factors = sorted(
            analysis.factors,
            key=lambda f: abs(f.weighted_value),
            reverse=True,
        )
        return sorted_factors[:top_n]
