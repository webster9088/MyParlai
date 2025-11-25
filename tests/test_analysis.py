"""Tests for analysis engine."""

from datetime import datetime

from src.models.team import Team, TeamStats
from src.models.matchup import Matchup, Odds, HeadToHead
from src.models.weather import create_dome_weather
from src.models.injury import Injury, InjuryReport, InjuryStatus
from src.models.parlay import BetType, PickConfidence

from src.analysis.factors import FactorAnalyzer, Factor, FactorAnalysis
from src.analysis.predictor import ParlayPredictor


def create_test_matchup():
    """Create a test matchup for analysis."""
    home_team = Team(
        id="nfl_kc",
        name="Chiefs",
        abbreviation="KC",
        city="Kansas City",
        sport="NFL",
        stats=TeamStats(wins=12, losses=5, points_for=400, points_against=300, streak=3),
    )

    away_team = Team(
        id="nfl_sf",
        name="49ers",
        abbreviation="SF",
        city="San Francisco",
        sport="NFL",
        stats=TeamStats(wins=11, losses=6, points_for=380, points_against=320, streak=-1),
    )

    return Matchup(
        id="nfl_20241125_kc_sf",
        sport="NFL",
        home_team=home_team,
        away_team=away_team,
        game_time=datetime.utcnow(),
        venue="Arrowhead Stadium",
        odds=Odds(spread=-3.5, moneyline_home=-175, moneyline_away=155, over_under=48.5),
        head_to_head=HeadToHead(home_wins=3, away_wins=2),
    )


class TestFactorAnalyzer:
    """Tests for FactorAnalyzer."""

    def test_analyze_matchup(self):
        """Test analyzing a matchup."""
        analyzer = FactorAnalyzer()
        matchup = create_test_matchup()

        analysis = analyzer.analyze(matchup)

        assert analysis.matchup_id == matchup.id
        assert len(analysis.factors) > 0
        assert analysis.confidence >= 0 and analysis.confidence <= 1

    def test_team_record_factor(self):
        """Test team record factor analysis."""
        analyzer = FactorAnalyzer()
        matchup = create_test_matchup()

        analysis = analyzer.analyze(matchup)

        record_factor = next(
            (f for f in analysis.factors if f.name == "team_record"), None
        )
        assert record_factor is not None
        # Home team has better record, so value should be positive
        assert record_factor.value > 0

    def test_home_advantage_factor(self):
        """Test home advantage factor."""
        analyzer = FactorAnalyzer()
        matchup = create_test_matchup()

        analysis = analyzer.analyze(matchup)

        home_factor = next(
            (f for f in analysis.factors if f.name == "home_advantage"), None
        )
        assert home_factor is not None
        assert home_factor.value > 0  # Home advantage should be positive

    def test_neutral_site(self):
        """Test neutral site removes home advantage."""
        analyzer = FactorAnalyzer()
        matchup = create_test_matchup()
        matchup.is_neutral_site = True

        analysis = analyzer.analyze(matchup)

        home_factor = next(
            (f for f in analysis.factors if f.name == "home_advantage"), None
        )
        assert home_factor is not None
        assert home_factor.value == 0

    def test_injury_factor(self):
        """Test injury factor analysis."""
        analyzer = FactorAnalyzer()
        matchup = create_test_matchup()

        # Add injuries to away team
        matchup.away_injuries = InjuryReport(
            team_id="nfl_sf",
            team_name="49ers",
            injuries=[
                Injury("p1", "Star QB", "nfl_sf", InjuryStatus.OUT, "knee", impact_score=0.5),
            ],
        )

        analysis = analyzer.analyze(matchup)

        injury_factor = next(
            (f for f in analysis.factors if f.name == "injuries"), None
        )
        assert injury_factor is not None
        # Away team has injuries, so factor should favor home
        assert injury_factor.value > 0

    def test_weather_factor_dome(self):
        """Test weather factor for dome games."""
        analyzer = FactorAnalyzer()
        matchup = create_test_matchup()
        matchup.weather = create_dome_weather()

        analysis = analyzer.analyze(matchup)

        weather_factor = next(
            (f for f in analysis.factors if f.name == "weather"), None
        )
        assert weather_factor is not None
        assert weather_factor.value == 0  # No impact for dome

    def test_get_key_factors(self):
        """Test getting key factors."""
        analyzer = FactorAnalyzer()
        matchup = create_test_matchup()

        analysis = analyzer.analyze(matchup)
        key_factors = analyzer.get_key_factors(analysis, top_n=3)

        assert len(key_factors) <= 3
        # Should be sorted by weighted value
        if len(key_factors) >= 2:
            assert abs(key_factors[0].weighted_value) >= abs(key_factors[1].weighted_value)


class TestParlayPredictor:
    """Tests for ParlayPredictor."""

    def test_analyze_matchup(self):
        """Test matchup analysis."""
        predictor = ParlayPredictor()
        matchup = create_test_matchup()

        analysis = predictor.analyze_matchup(matchup)

        assert analysis is not None
        assert analysis.confidence > 0

    def test_predict_spread(self):
        """Test spread prediction."""
        predictor = ParlayPredictor()
        matchup = create_test_matchup()
        analysis = predictor.analyze_matchup(matchup)

        pick = predictor.predict_spread(matchup, analysis)

        assert pick.bet_type == BetType.SPREAD
        assert pick.pick is not None
        assert pick.confidence in PickConfidence
        assert len(pick.reasoning) > 0

    def test_predict_moneyline(self):
        """Test moneyline prediction."""
        predictor = ParlayPredictor()
        matchup = create_test_matchup()
        analysis = predictor.analyze_matchup(matchup)

        pick = predictor.predict_moneyline(matchup, analysis)

        assert pick.bet_type == BetType.MONEYLINE
        assert "ML" in pick.pick
        assert pick.team_id is not None

    def test_predict_total(self):
        """Test total prediction."""
        predictor = ParlayPredictor()
        matchup = create_test_matchup()
        analysis = predictor.analyze_matchup(matchup)

        pick = predictor.predict_total(matchup, analysis)

        assert pick.bet_type in [BetType.OVER, BetType.UNDER]
        assert "OVER" in pick.pick or "UNDER" in pick.pick

    def test_generate_parlay(self):
        """Test parlay generation."""
        predictor = ParlayPredictor()
        matchups = [create_test_matchup()]

        parlay = predictor.generate_parlay(matchups, num_legs=1)

        assert parlay is not None
        assert len(parlay.legs) >= 1
        assert parlay.stake > 0
        assert parlay.total_odds > 1

    def test_generate_safe_parlay(self):
        """Test safe parlay generation."""
        predictor = ParlayPredictor()
        matchups = [create_test_matchup()]

        parlay = predictor.generate_safe_parlay(matchups)

        assert parlay is not None
        # Safe parlays should have higher confidence legs
        for leg in parlay.legs:
            assert leg.confidence_score >= 0.5

    def test_confidence_levels(self):
        """Test confidence level assignment."""
        predictor = ParlayPredictor()

        assert predictor._get_confidence_level(0.75) == PickConfidence.VERY_HIGH
        assert predictor._get_confidence_level(0.65) == PickConfidence.HIGH
        assert predictor._get_confidence_level(0.55) == PickConfidence.MEDIUM
        assert predictor._get_confidence_level(0.35) == PickConfidence.LOW

    def test_parlay_summary(self):
        """Test parlay summary generation."""
        predictor = ParlayPredictor()
        matchups = [create_test_matchup()]

        parlay = predictor.generate_parlay(matchups, num_legs=1)
        summary = parlay.get_summary()

        assert "Parlay" in summary
        assert "Stake" in summary
        assert "Odds" in summary


class TestFactor:
    """Tests for Factor dataclass."""

    def test_weighted_value(self):
        """Test weighted value calculation."""
        factor = Factor(
            name="test",
            value=0.5,
            weight=0.2,
        )
        assert factor.weighted_value == 0.1

    def test_weighted_value_negative(self):
        """Test weighted value with negative value."""
        factor = Factor(
            name="test",
            value=-0.5,
            weight=0.2,
        )
        assert factor.weighted_value == -0.1


class TestFactorAnalysis:
    """Tests for FactorAnalysis dataclass."""

    def test_add_factor_positive(self):
        """Test adding positive factor."""
        analysis = FactorAnalysis(matchup_id="test")
        factor = Factor("test", value=0.5, weight=0.2)

        analysis.add_factor(factor)

        assert len(analysis.factors) == 1
        assert analysis.home_score == 0.1  # 0.5 * 0.2

    def test_add_factor_negative(self):
        """Test adding negative factor."""
        analysis = FactorAnalysis(matchup_id="test")
        factor = Factor("test", value=-0.5, weight=0.2)

        analysis.add_factor(factor)

        assert len(analysis.factors) == 1
        assert analysis.away_score == 0.1  # abs(-0.1)

    def test_calculate_prediction(self):
        """Test prediction calculation."""
        analysis = FactorAnalysis(matchup_id="test")
        analysis.home_score = 0.6
        analysis.away_score = 0.4

        analysis.calculate_prediction()

        # Home has 60% of scores, so confidence should be >= 0.5
        assert analysis.confidence >= 0.5
        assert analysis.confidence <= 1.0
