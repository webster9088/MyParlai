"""Tests for services."""

from datetime import datetime

from src.services.sports_data import SportsDataService
from src.services.weather_service import WeatherService
from src.services.odds_service import OddsService


class TestSportsDataService:
    """Tests for SportsDataService."""

    def test_get_teams_nfl(self):
        """Test getting NFL teams."""
        service = SportsDataService()
        try:
            teams = service.get_teams("nfl")
            assert len(teams) > 0
            assert all(t.sport == "NFL" for t in teams)
        finally:
            service.close()

    def test_get_teams_nba(self):
        """Test getting NBA teams."""
        service = SportsDataService()
        try:
            teams = service.get_teams("nba")
            assert len(teams) > 0
            assert all(t.sport == "NBA" for t in teams)
        finally:
            service.close()

    def test_get_team_by_id(self):
        """Test getting a specific team."""
        service = SportsDataService()
        try:
            team = service.get_team("nfl", "nfl_kc")
            assert team is not None
            assert team.abbreviation == "KC"
        finally:
            service.close()

    def test_get_matchups(self):
        """Test getting matchups."""
        service = SportsDataService()
        try:
            matchups = service.get_matchups("nfl")
            assert len(matchups) > 0
            for matchup in matchups:
                assert matchup.home_team is not None
                assert matchup.away_team is not None
                assert matchup.odds is not None
        finally:
            service.close()

    def test_get_injury_report(self):
        """Test getting injury report."""
        service = SportsDataService()
        try:
            report = service.get_injury_report("nfl", "nfl_kc")
            assert report is not None
            assert report.team_id == "nfl_kc"
        finally:
            service.close()

    def test_get_head_to_head(self):
        """Test getting head-to-head record."""
        service = SportsDataService()
        try:
            h2h = service.get_head_to_head("nfl", "nfl_kc", "nfl_sf")
            assert h2h is not None
            assert h2h.total_games >= 0
        finally:
            service.close()

    def test_caching(self):
        """Test that caching works."""
        service = SportsDataService()
        try:
            # First call
            teams1 = service.get_teams("nfl")
            # Second call should return cached
            teams2 = service.get_teams("nfl")
            assert teams1 == teams2
        finally:
            service.close()


class TestWeatherService:
    """Tests for WeatherService."""

    def test_is_dome_venue_nba(self):
        """Test that NBA venues are always indoor."""
        service = WeatherService()
        assert service.is_dome_venue("TD Garden", "NBA") is True
        assert service.is_dome_venue("Any Arena", "NBA") is True

    def test_is_dome_venue_nfl_dome(self):
        """Test NFL dome venues."""
        service = WeatherService()
        assert service.is_dome_venue("AT&T Stadium", "NFL") is True
        assert service.is_dome_venue("Allegiant Stadium", "NFL") is True

    def test_is_dome_venue_nfl_outdoor(self):
        """Test NFL outdoor venues."""
        service = WeatherService()
        assert service.is_dome_venue("Arrowhead Stadium", "NFL") is False

    def test_get_weather_dome(self):
        """Test getting weather for dome venue."""
        service = WeatherService()
        try:
            weather = service.get_weather(
                location="Las Vegas",
                game_time=datetime.utcnow(),
                venue="Allegiant Stadium",
                sport="NFL",
            )
            assert weather.is_dome is True
            assert weather.get_impact_score() == 0.0
        finally:
            service.close()

    def test_get_weather_outdoor(self):
        """Test getting weather for outdoor venue."""
        service = WeatherService()
        try:
            weather = service.get_weather(
                location="Green Bay",
                game_time=datetime.utcnow(),
                venue="Lambeau Field",
                sport="NFL",
            )
            assert weather.is_dome is False
            assert weather.temperature < 40  # Cold in Green Bay
        finally:
            service.close()

    def test_get_weather_impact(self):
        """Test weather impact analysis."""
        service = WeatherService()
        try:
            weather = service.get_weather(
                location="Buffalo",
                game_time=datetime.utcnow(),
                venue="Highmark Stadium",
                sport="NFL",
            )
            impacts = service.get_weather_impact(weather, "NFL")
            assert "passing_impact" in impacts
            assert "kicking_impact" in impacts
            assert "total_impact" in impacts
        finally:
            service.close()


class TestOddsService:
    """Tests for OddsService."""

    def test_get_odds_nfl(self):
        """Test getting NFL odds."""
        service = OddsService()
        try:
            odds = service.get_odds("NFL")
            assert len(odds) > 0
            for game_odds in odds:
                assert "home_team" in game_odds
                assert "away_team" in game_odds
                assert "spread" in game_odds
        finally:
            service.close()

    def test_get_matchup_odds(self):
        """Test getting odds for specific matchup."""
        service = OddsService()
        try:
            odds = service.get_matchup_odds("NFL", "Chiefs", "49ers")
            assert odds is not None
            assert odds.spread != 0 or odds.moneyline_home != -110
        finally:
            service.close()

    def test_get_consensus_pick(self):
        """Test getting consensus betting data."""
        service = OddsService()
        try:
            consensus = service.get_consensus_pick("NFL", "test_matchup")
            assert "spread_home_pct" in consensus
            assert "ml_home_pct" in consensus
            assert "over_pct" in consensus
        finally:
            service.close()

    def test_caching(self):
        """Test that odds caching works."""
        service = OddsService()
        try:
            odds1 = service.get_odds("NFL")
            odds2 = service.get_odds("NFL")
            assert odds1 == odds2
        finally:
            service.close()
