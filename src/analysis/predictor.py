"""AI-powered parlay prediction engine."""

import uuid
from datetime import datetime
from typing import List, Optional, Tuple

from src.models.matchup import Matchup
from src.models.parlay import Parlay, ParlayLeg, BetType, PickConfidence
from src.analysis.factors import FactorAnalyzer, FactorAnalysis


class ParlayPredictor:
    """AI-powered parlay prediction engine.

    This class uses factor analysis and historical data to generate
    intelligent parlay picks with confidence ratings.
    """

    # Confidence thresholds
    CONFIDENCE_THRESHOLDS = {
        PickConfidence.VERY_HIGH: 0.70,
        PickConfidence.HIGH: 0.60,
        PickConfidence.MEDIUM: 0.50,
        PickConfidence.LOW: 0.0,
    }

    def __init__(self, factor_analyzer: Optional[FactorAnalyzer] = None):
        """Initialize the predictor.

        Args:
            factor_analyzer: Custom factor analyzer. If None, uses default.
        """
        self.factor_analyzer = factor_analyzer or FactorAnalyzer()

    def analyze_matchup(self, matchup: Matchup) -> FactorAnalysis:
        """Analyze a single matchup.

        Args:
            matchup: The matchup to analyze.

        Returns:
            Factor analysis for the matchup.
        """
        return self.factor_analyzer.analyze(matchup)

    def predict_spread(self, matchup: Matchup, analysis: FactorAnalysis) -> ParlayLeg:
        """Generate a spread pick for a matchup.

        Args:
            matchup: The matchup.
            analysis: Pre-computed factor analysis.

        Returns:
            ParlayLeg with spread pick.
        """
        spread = matchup.odds.spread

        # Determine if we should take home or away
        score_diff = analysis.home_score - analysis.away_score
        take_home = score_diff > 0

        # Adjust confidence based on spread value
        base_confidence = analysis.confidence

        # If the line seems off from our analysis, increase confidence
        if take_home and spread < -7:
            # Line says home is big favorite, but we like them
            base_confidence *= 0.9  # Slight reduction
        elif not take_home and spread > 7:
            base_confidence *= 0.9

        confidence = self._get_confidence_level(base_confidence)

        if take_home:
            pick = f"{matchup.home_team.abbreviation} {spread:+.1f}"
            team_id = matchup.home_team.id
        else:
            pick = f"{matchup.away_team.abbreviation} {-spread:+.1f}"
            team_id = matchup.away_team.id

        key_factors = self.factor_analyzer.get_key_factors(analysis)

        return ParlayLeg(
            matchup_id=matchup.id,
            bet_type=BetType.SPREAD,
            pick=pick,
            odds=matchup.odds.spread_odds,
            team_id=team_id,
            confidence=confidence,
            confidence_score=base_confidence,
            reasoning=self._generate_reasoning(analysis, "spread", take_home),
            key_factors=[f.description for f in key_factors],
        )

    def predict_moneyline(self, matchup: Matchup, analysis: FactorAnalysis) -> ParlayLeg:
        """Generate a moneyline pick for a matchup.

        Args:
            matchup: The matchup.
            analysis: Pre-computed factor analysis.

        Returns:
            ParlayLeg with moneyline pick.
        """
        # Determine winner based on analysis
        take_home = analysis.home_score > analysis.away_score

        # Moneyline confidence should be higher for clear favorites
        base_confidence = analysis.confidence

        if take_home:
            pick = f"{matchup.home_team.abbreviation} ML"
            team_id = matchup.home_team.id
            odds = matchup.odds.moneyline_home
        else:
            pick = f"{matchup.away_team.abbreviation} ML"
            team_id = matchup.away_team.id
            odds = matchup.odds.moneyline_away

        confidence = self._get_confidence_level(base_confidence)
        key_factors = self.factor_analyzer.get_key_factors(analysis)

        return ParlayLeg(
            matchup_id=matchup.id,
            bet_type=BetType.MONEYLINE,
            pick=pick,
            odds=odds,
            team_id=team_id,
            confidence=confidence,
            confidence_score=base_confidence,
            reasoning=self._generate_reasoning(analysis, "moneyline", take_home),
            key_factors=[f.description for f in key_factors],
        )

    def predict_total(self, matchup: Matchup, analysis: FactorAnalysis) -> ParlayLeg:
        """Generate an over/under pick for a matchup.

        Args:
            matchup: The matchup.
            analysis: Pre-computed factor analysis.

        Returns:
            ParlayLeg with over/under pick.
        """
        total = matchup.odds.over_under

        # Analyze factors that affect scoring
        take_over = self._analyze_total(matchup, analysis)

        # Total predictions are generally less confident
        base_confidence = analysis.confidence * 0.85

        if take_over:
            pick = f"OVER {total}"
            bet_type = BetType.OVER
            odds = matchup.odds.over_odds
        else:
            pick = f"UNDER {total}"
            bet_type = BetType.UNDER
            odds = matchup.odds.under_odds

        confidence = self._get_confidence_level(base_confidence)

        return ParlayLeg(
            matchup_id=matchup.id,
            bet_type=bet_type,
            pick=pick,
            odds=odds,
            confidence=confidence,
            confidence_score=base_confidence,
            reasoning=self._generate_total_reasoning(matchup, take_over),
            key_factors=self._get_total_factors(matchup),
        )

    def generate_parlay(
        self,
        matchups: List[Matchup],
        num_legs: int = 3,
        bet_types: Optional[List[BetType]] = None,
        min_confidence: float = 0.5,
        stake: float = 10.0,
    ) -> Parlay:
        """Generate an AI-powered parlay from available matchups.

        Args:
            matchups: List of available matchups.
            num_legs: Target number of legs in the parlay.
            bet_types: Allowed bet types. Defaults to spread and moneyline.
            min_confidence: Minimum confidence threshold for picks.
            stake: Wager amount.

        Returns:
            Generated Parlay with picks.
        """
        if bet_types is None:
            bet_types = [BetType.SPREAD, BetType.MONEYLINE]

        # Analyze all matchups
        analyses: List[Tuple[Matchup, FactorAnalysis]] = []
        for matchup in matchups:
            analysis = self.analyze_matchup(matchup)
            if analysis.confidence >= min_confidence:
                analyses.append((matchup, analysis))

        # Sort by confidence
        analyses.sort(key=lambda x: x[1].confidence, reverse=True)

        # Generate picks
        legs = []
        for matchup, analysis in analyses[:num_legs]:
            # Choose best bet type for this matchup
            best_leg = self._choose_best_bet(matchup, analysis, bet_types)
            if best_leg:
                legs.append(best_leg)

        # Determine sport
        sports = set(m.sport for m, _ in analyses[:num_legs])
        sport = list(sports)[0] if len(sports) == 1 else "mixed"

        parlay = Parlay(
            id=str(uuid.uuid4())[:8],
            legs=legs,
            stake=stake,
            sport=sport,
            name=f"AI Parlay - {datetime.utcnow().strftime('%Y-%m-%d')}",
        )

        return parlay

    def generate_safe_parlay(
        self,
        matchups: List[Matchup],
        stake: float = 10.0,
    ) -> Parlay:
        """Generate a conservative parlay with higher confidence picks.

        Args:
            matchups: List of available matchups.
            stake: Wager amount.

        Returns:
            Generated Parlay with conservative picks.
        """
        return self.generate_parlay(
            matchups=matchups,
            num_legs=2,
            bet_types=[BetType.SPREAD, BetType.MONEYLINE],
            min_confidence=0.60,
            stake=stake,
        )

    def generate_aggressive_parlay(
        self,
        matchups: List[Matchup],
        stake: float = 10.0,
    ) -> Parlay:
        """Generate an aggressive parlay with more legs.

        Args:
            matchups: List of available matchups.
            stake: Wager amount.

        Returns:
            Generated Parlay with aggressive picks.
        """
        return self.generate_parlay(
            matchups=matchups,
            num_legs=5,
            bet_types=[BetType.SPREAD, BetType.MONEYLINE, BetType.OVER, BetType.UNDER],
            min_confidence=0.45,
            stake=stake,
        )

    def _choose_best_bet(
        self,
        matchup: Matchup,
        analysis: FactorAnalysis,
        allowed_types: List[BetType],
    ) -> Optional[ParlayLeg]:
        """Choose the best bet type for a matchup."""
        candidates = []

        if BetType.SPREAD in allowed_types:
            candidates.append(self.predict_spread(matchup, analysis))

        if BetType.MONEYLINE in allowed_types:
            candidates.append(self.predict_moneyline(matchup, analysis))

        if BetType.OVER in allowed_types or BetType.UNDER in allowed_types:
            total_leg = self.predict_total(matchup, analysis)
            if total_leg.bet_type in allowed_types:
                candidates.append(total_leg)

        if not candidates:
            return None

        # Return the pick with highest confidence
        return max(candidates, key=lambda x: x.confidence_score)

    def _get_confidence_level(self, score: float) -> PickConfidence:
        """Convert numerical confidence to enum level."""
        for level, threshold in self.CONFIDENCE_THRESHOLDS.items():
            if score >= threshold:
                return level
        return PickConfidence.LOW

    def _analyze_total(self, matchup: Matchup, analysis: FactorAnalysis) -> bool:
        """Determine if the game will go over or under.

        Returns True for over, False for under.
        """
        # Factors that suggest higher scoring
        over_indicators = 0

        # Good offenses tend to score more
        if matchup.home_team.stats.points_for > 25 * 17:  # Above average
            over_indicators += 1
        if matchup.away_team.stats.points_for > 25 * 17:
            over_indicators += 1

        # Poor defenses allow more points
        if matchup.home_team.stats.points_against > 23 * 17:
            over_indicators += 1
        if matchup.away_team.stats.points_against > 23 * 17:
            over_indicators += 1

        # Weather affects scoring
        if matchup.weather and not matchup.weather.is_dome:
            if matchup.weather.affects_gameplay:
                over_indicators -= 1

        return over_indicators >= 2

    def _generate_reasoning(
        self,
        analysis: FactorAnalysis,
        bet_type: str,
        take_home: bool,
    ) -> str:
        """Generate human-readable reasoning for a pick."""
        key_factors = self.factor_analyzer.get_key_factors(analysis)
        team_type = "home team" if take_home else "away team"

        reasons = [f.description for f in key_factors if f.description]
        reason_text = "; ".join(reasons) if reasons else "Balanced analysis"

        return f"Taking {team_type} on {bet_type}: {reason_text}"

    def _generate_total_reasoning(self, matchup: Matchup, take_over: bool) -> str:
        """Generate reasoning for total pick."""
        direction = "over" if take_over else "under"
        return f"Expecting game to go {direction} based on team scoring trends"

    def _get_total_factors(self, matchup: Matchup) -> List[str]:
        """Get factors relevant to total prediction."""
        factors = []

        home_ppg = matchup.home_team.stats.points_for / max(
            matchup.home_team.stats.wins + matchup.home_team.stats.losses, 1
        )
        away_ppg = matchup.away_team.stats.points_for / max(
            matchup.away_team.stats.wins + matchup.away_team.stats.losses, 1
        )

        factors.append(f"Home team averaging {home_ppg:.1f} points per game")
        factors.append(f"Away team averaging {away_ppg:.1f} points per game")

        if matchup.weather and not matchup.weather.is_dome:
            if matchup.weather.affects_gameplay:
                factors.append(f"Weather may impact scoring: {matchup.weather.conditions}")

        return factors
