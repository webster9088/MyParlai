"""Tests for data models."""

import pytest

from src.models.sport import Sport, SportType
from src.models.team import Team, TeamStats
from src.models.player import Player
from src.models.weather import Weather, create_dome_weather
from src.models.injury import Injury, InjuryReport, InjuryStatus
from src.models.parlay import Parlay, ParlayLeg, BetType


class TestSport:
    """Tests for Sport model."""

    def test_from_string_nfl(self):
        """Test creating NFL sport from string."""
        sport = Sport.from_string("nfl")
        assert sport.sport_type == SportType.NFL
        assert sport.weather_affects is True
        assert "weather" in sport.factors

    def test_from_string_nba(self):
        """Test creating NBA sport from string."""
        sport = Sport.from_string("nba")
        assert sport.sport_type == SportType.NBA
        assert sport.weather_affects is False
        assert "back_to_back" in sport.factors

    def test_from_string_invalid(self):
        """Test that invalid sport raises ValueError."""
        with pytest.raises(ValueError, match="Unknown sport"):
            Sport.from_string("invalid_sport")

    def test_default_factors_included(self):
        """Test that default factors are included."""
        sport = Sport.from_string("nfl")
        assert "team_record" in sport.factors
        assert "injuries" in sport.factors


class TestTeam:
    """Tests for Team model."""

    def test_full_name(self):
        """Test full team name property."""
        team = Team(
            id="nfl_kc",
            name="Chiefs",
            abbreviation="KC",
            city="Kansas City",
            sport="NFL",
        )
        assert team.full_name == "Kansas City Chiefs"

    def test_get_record(self):
        """Test record formatting."""
        team = Team(
            id="nfl_kc",
            name="Chiefs",
            abbreviation="KC",
            city="Kansas City",
            sport="NFL",
            stats=TeamStats(wins=12, losses=5),
        )
        assert team.get_record() == "12-5"

    def test_get_record_with_ties(self):
        """Test record formatting with ties."""
        team = Team(
            id="nfl_kc",
            name="Chiefs",
            abbreviation="KC",
            city="Kansas City",
            sport="NFL",
            stats=TeamStats(wins=10, losses=5, ties=2),
        )
        assert team.get_record() == "10-5-2"

    def test_win_percentage(self):
        """Test win percentage calculation."""
        stats = TeamStats(wins=12, losses=4)
        assert stats.win_percentage == 0.75

    def test_point_differential(self):
        """Test point differential calculation."""
        stats = TeamStats(points_for=400, points_against=300)
        assert stats.point_differential == 100


class TestPlayer:
    """Tests for Player model."""

    def test_is_active(self):
        """Test active status check."""
        player = Player(
            id="p1",
            name="Test Player",
            team_id="team1",
            position="QB",
            status="active",
        )
        assert player.is_active is True

    def test_is_injured(self):
        """Test injured status check."""
        player = Player(
            id="p1",
            name="Test Player",
            team_id="team1",
            position="QB",
            status="questionable",
        )
        assert player.is_injured is True
        assert player.is_active is False


class TestWeather:
    """Tests for Weather model."""

    def test_dome_weather(self):
        """Test dome weather creation."""
        weather = create_dome_weather()
        assert weather.is_dome is True
        assert weather.is_severe is False
        assert weather.affects_gameplay is False
        assert weather.get_impact_score() == 0.0

    def test_severe_weather(self):
        """Test severe weather detection."""
        weather = Weather(
            temperature=15.0,
            feels_like=5.0,
            humidity=80.0,
            wind_speed=30.0,
            wind_direction="N",
            precipitation_chance=80.0,
            conditions="Blizzard",
        )
        assert weather.is_severe is True
        assert weather.affects_gameplay is True

    def test_normal_weather(self):
        """Test normal weather conditions."""
        weather = Weather(
            temperature=65.0,
            feels_like=65.0,
            humidity=50.0,
            wind_speed=5.0,
            wind_direction="SW",
            precipitation_chance=10.0,
            conditions="Clear",
        )
        assert weather.is_severe is False
        assert weather.affects_gameplay is False

    def test_impact_score_range(self):
        """Test impact score is within valid range."""
        weather = Weather(
            temperature=20.0,
            feels_like=10.0,
            humidity=90.0,
            wind_speed=35.0,
            wind_direction="N",
            precipitation_chance=90.0,
            conditions="Storm",
        )
        score = weather.get_impact_score()
        assert 0 <= score <= 1


class TestInjury:
    """Tests for Injury model."""

    def test_is_likely_out(self):
        """Test likely out status."""
        injury = Injury(
            player_id="p1",
            player_name="Test Player",
            team_id="team1",
            status=InjuryStatus.OUT,
            injury_type="knee",
        )
        assert injury.is_likely_out is True

    def test_is_uncertain(self):
        """Test uncertain status."""
        injury = Injury(
            player_id="p1",
            player_name="Test Player",
            team_id="team1",
            status=InjuryStatus.QUESTIONABLE,
            injury_type="ankle",
        )
        assert injury.is_uncertain is True
        assert injury.is_likely_out is False


class TestInjuryReport:
    """Tests for InjuryReport model."""

    def test_total_injuries(self):
        """Test total injuries count."""
        report = InjuryReport(
            team_id="team1",
            team_name="Team 1",
            injuries=[
                Injury("p1", "Player 1", "team1", InjuryStatus.OUT, "knee"),
                Injury("p2", "Player 2", "team1", InjuryStatus.QUESTIONABLE, "ankle"),
            ],
        )
        assert report.total_injuries == 2

    def test_players_out(self):
        """Test players out filtering."""
        report = InjuryReport(
            team_id="team1",
            team_name="Team 1",
            injuries=[
                Injury("p1", "Player 1", "team1", InjuryStatus.OUT, "knee"),
                Injury("p2", "Player 2", "team1", InjuryStatus.QUESTIONABLE, "ankle"),
                Injury("p3", "Player 3", "team1", InjuryStatus.PROBABLE, "hamstring"),
            ],
        )
        assert len(report.players_out) == 1
        assert len(report.players_questionable) == 1

    def test_total_impact(self):
        """Test total impact calculation."""
        report = InjuryReport(
            team_id="team1",
            team_name="Team 1",
            injuries=[
                Injury(
                    "p1", "Player 1", "team1", InjuryStatus.OUT, "knee", impact_score=0.4
                ),
                Injury(
                    "p2", "Player 2", "team1", InjuryStatus.QUESTIONABLE, "ankle", impact_score=0.3
                ),
            ],
        )
        # OUT player: 0.4, QUESTIONABLE: 0.3 * 0.5 = 0.15
        assert report.get_total_impact() == pytest.approx(0.55, rel=0.01)


class TestParlayLeg:
    """Tests for ParlayLeg model."""

    def test_implied_probability_negative_odds(self):
        """Test implied probability for favorite."""
        leg = ParlayLeg(
            matchup_id="m1",
            bet_type=BetType.SPREAD,
            pick="KC -3.5",
            odds=-110,
        )
        assert leg.implied_probability == pytest.approx(0.524, rel=0.01)

    def test_implied_probability_positive_odds(self):
        """Test implied probability for underdog."""
        leg = ParlayLeg(
            matchup_id="m1",
            bet_type=BetType.MONEYLINE,
            pick="SF ML",
            odds=150,
        )
        assert leg.implied_probability == pytest.approx(0.4, rel=0.01)

    def test_decimal_odds_conversion(self):
        """Test decimal odds conversion."""
        leg = ParlayLeg(
            matchup_id="m1",
            bet_type=BetType.SPREAD,
            pick="KC -3.5",
            odds=-110,
        )
        assert leg.decimal_odds == pytest.approx(1.909, rel=0.01)


class TestParlay:
    """Tests for Parlay model."""

    def test_total_odds(self):
        """Test total parlay odds calculation."""
        parlay = Parlay(
            id="test",
            legs=[
                ParlayLeg("m1", BetType.SPREAD, "KC -3.5", odds=-110),
                ParlayLeg("m2", BetType.SPREAD, "BUF -2.5", odds=-110),
            ],
        )
        # Each leg at -110 is ~1.909 decimal
        # Combined: 1.909 * 1.909 ≈ 3.645
        assert parlay.total_odds == pytest.approx(3.645, rel=0.05)

    def test_potential_payout(self):
        """Test potential payout calculation."""
        parlay = Parlay(
            id="test",
            legs=[
                ParlayLeg("m1", BetType.SPREAD, "KC -3.5", odds=-110),
            ],
            stake=100.0,
        )
        # 1.909 * 100 ≈ $190.9
        assert parlay.potential_payout == pytest.approx(190.9, rel=0.05)

    def test_potential_profit(self):
        """Test potential profit calculation."""
        parlay = Parlay(
            id="test",
            legs=[
                ParlayLeg("m1", BetType.SPREAD, "KC -3.5", odds=-110),
            ],
            stake=100.0,
        )
        profit = parlay.potential_profit
        assert profit == pytest.approx(90.9, rel=0.05)

    def test_average_confidence(self):
        """Test average confidence calculation."""
        parlay = Parlay(
            id="test",
            legs=[
                ParlayLeg("m1", BetType.SPREAD, "KC -3.5", confidence_score=0.6),
                ParlayLeg("m2", BetType.SPREAD, "BUF -2.5", confidence_score=0.8),
            ],
        )
        assert parlay.average_confidence == 0.7

    def test_american_odds_favorite(self):
        """Test American odds for parlay as favorite."""
        parlay = Parlay(
            id="test",
            legs=[
                ParlayLeg("m1", BetType.SPREAD, "KC -3.5", odds=-110),
                ParlayLeg("m2", BetType.SPREAD, "BUF -2.5", odds=-110),
            ],
        )
        # Decimal ~3.645 should give positive American odds
        assert parlay.get_american_odds() > 0
