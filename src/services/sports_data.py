"""Service for fetching sports data including matchups, teams, and injuries."""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass

import requests

from src.models.team import Team, TeamStats
from src.models.matchup import Matchup, Odds, HeadToHead
from src.models.injury import Injury, InjuryReport, InjuryStatus


@dataclass
class APIConfig:
    """Configuration for sports data API.

    Attributes:
        base_url: Base URL for the API.
        api_key: API key for authentication.
        timeout: Request timeout in seconds.
    """

    base_url: str = "https://api.sportsdata.io"
    api_key: Optional[str] = None
    timeout: int = 30

    @classmethod
    def from_env(cls) -> "APIConfig":
        """Create config from environment variables."""
        return cls(
            base_url=os.getenv("SPORTS_API_BASE_URL", "https://api.sportsdata.io"),
            api_key=os.getenv("SPORTS_API_KEY"),
            timeout=int(os.getenv("SPORTS_API_TIMEOUT", "30")),
        )


class SportsDataService:
    """Service for fetching sports data from external APIs.

    This service provides methods to retrieve teams, players, matchups,
    and injury reports for various sports.
    """

    def __init__(self, config: Optional[APIConfig] = None):
        """Initialize the sports data service.

        Args:
            config: API configuration. If None, loads from environment.
        """
        self.config = config or APIConfig.from_env()
        self._session = None
        self._cache: Dict[str, tuple] = {}
        self._cache_ttl = 300  # 5 minutes

    def _get_session(self) -> requests.Session:
        """Get or create a requests session."""
        if self._session is None:
            self._session = requests.Session()
            if self.config.api_key:
                self._session.headers["Authorization"] = f"Bearer {self.config.api_key}"
        return self._session

    def _get_cached(self, key: str) -> Optional[any]:
        """Get cached data if still valid."""
        if key in self._cache:
            data, timestamp = self._cache[key]
            if datetime.utcnow().timestamp() - timestamp < self._cache_ttl:
                return data
            del self._cache[key]
        return None

    def _set_cached(self, key: str, data: any) -> None:
        """Cache data with current timestamp."""
        self._cache[key] = (data, datetime.utcnow().timestamp())

    def get_teams(self, sport: str) -> List[Team]:
        """Get all teams for a sport.

        Args:
            sport: Sport identifier (e.g., "nfl", "nba").

        Returns:
            List of Team objects.

        Note:
            Returns mock data if API is not configured.
        """
        cache_key = f"teams_{sport}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        # Return mock data for demonstration
        teams = self._get_mock_teams(sport)
        self._set_cached(cache_key, teams)
        return teams

    def get_team(self, sport: str, team_id: str) -> Optional[Team]:
        """Get a specific team by ID.

        Args:
            sport: Sport identifier.
            team_id: Team identifier.

        Returns:
            Team object or None if not found.
        """
        teams = self.get_teams(sport)
        for team in teams:
            if team.id == team_id:
                return team
        return None

    def get_matchups(
        self,
        sport: str,
        date: Optional[datetime] = None,
        include_odds: bool = True,
    ) -> List[Matchup]:
        """Get matchups for a sport on a specific date.

        Args:
            sport: Sport identifier.
            date: Date for matchups. Defaults to today.
            include_odds: Whether to include betting odds.

        Returns:
            List of Matchup objects.
        """
        if date is None:
            date = datetime.utcnow()

        cache_key = f"matchups_{sport}_{date.strftime('%Y-%m-%d')}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        # Return mock data for demonstration
        matchups = self._get_mock_matchups(sport, date)
        self._set_cached(cache_key, matchups)
        return matchups

    def get_injury_report(self, sport: str, team_id: str) -> InjuryReport:
        """Get injury report for a team.

        Args:
            sport: Sport identifier.
            team_id: Team identifier.

        Returns:
            InjuryReport for the team.
        """
        cache_key = f"injuries_{sport}_{team_id}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        # Return mock data for demonstration
        report = self._get_mock_injury_report(team_id)
        self._set_cached(cache_key, report)
        return report

    def get_head_to_head(
        self,
        sport: str,
        team1_id: str,
        team2_id: str,
        num_games: int = 10,
    ) -> HeadToHead:
        """Get head-to-head record between two teams.

        Args:
            sport: Sport identifier.
            team1_id: First team ID (considered home).
            team2_id: Second team ID (considered away).
            num_games: Number of recent games to consider.

        Returns:
            HeadToHead record.
        """
        cache_key = f"h2h_{sport}_{team1_id}_{team2_id}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        # Return mock data for demonstration
        h2h = HeadToHead(
            home_wins=3,
            away_wins=2,
            ties=0,
            last_meeting=datetime.utcnow() - timedelta(days=30),
            last_winner=team1_id,
            avg_total_points=48.5,
        )
        self._set_cached(cache_key, h2h)
        return h2h

    def _get_mock_teams(self, sport: str) -> List[Team]:
        """Generate mock team data for demonstration."""
        mock_data = {
            "nfl": [
                ("KC", "Chiefs", "Kansas City", "AFC", "West", 12, 5),
                ("SF", "49ers", "San Francisco", "NFC", "West", 11, 6),
                ("BUF", "Bills", "Buffalo", "AFC", "East", 10, 7),
                ("DAL", "Cowboys", "Dallas", "NFC", "East", 9, 8),
                ("MIA", "Dolphins", "Miami", "AFC", "East", 11, 6),
                ("PHI", "Eagles", "Philadelphia", "NFC", "East", 10, 7),
                ("BAL", "Ravens", "Baltimore", "AFC", "North", 13, 4),
                ("DET", "Lions", "Detroit", "NFC", "North", 12, 5),
            ],
            "nba": [
                ("BOS", "Celtics", "Boston", "Eastern", "Atlantic", 45, 12),
                ("DEN", "Nuggets", "Denver", "Western", "Northwest", 42, 15),
                ("MIL", "Bucks", "Milwaukee", "Eastern", "Central", 40, 17),
                ("OKC", "Thunder", "Oklahoma City", "Western", "Northwest", 41, 16),
                ("PHX", "Suns", "Phoenix", "Western", "Pacific", 35, 22),
                ("LAL", "Lakers", "Los Angeles", "Western", "Pacific", 33, 24),
            ],
        }

        teams = []
        sport_data = mock_data.get(sport.lower(), mock_data["nfl"])

        for abbr, name, city, conf, div, wins, losses in sport_data:
            team = Team(
                id=f"{sport.lower()}_{abbr.lower()}",
                name=name,
                abbreviation=abbr,
                city=city,
                sport=sport.upper(),
                conference=conf,
                division=div,
                stats=TeamStats(
                    wins=wins,
                    losses=losses,
                    points_for=wins * 25,
                    points_against=losses * 20,
                ),
            )
            teams.append(team)

        return teams

    def _get_mock_matchups(self, sport: str, date: datetime) -> List[Matchup]:
        """Generate mock matchup data for demonstration."""
        teams = self.get_teams(sport)
        matchups = []

        # Create matchups from pairs of teams
        for i in range(0, len(teams) - 1, 2):
            home_team = teams[i]
            away_team = teams[i + 1]

            # Get injury reports
            home_injuries = self.get_injury_report(sport, home_team.id)
            away_injuries = self.get_injury_report(sport, away_team.id)

            # Get head-to-head
            h2h = self.get_head_to_head(sport, home_team.id, away_team.id)

            matchup_id = (f"{sport}_{date.strftime('%Y%m%d')}"
                          f"_{home_team.abbreviation}_{away_team.abbreviation}")
            home_is_better = home_team.stats.win_percentage > away_team.stats.win_percentage
            home_is_winning = home_team.stats.win_percentage > 0.5
            matchup = Matchup(
                id=matchup_id,
                sport=sport.upper(),
                home_team=home_team,
                away_team=away_team,
                game_time=date.replace(hour=13 + i, minute=0),
                venue=f"{home_team.city} Stadium",
                odds=Odds(
                    spread=-3.5 if home_is_better else 3.5,
                    moneyline_home=-150 if home_is_winning else 130,
                    moneyline_away=130 if home_is_winning else -150,
                    over_under=45.5 + i * 2,
                ),
                home_injuries=home_injuries,
                away_injuries=away_injuries,
                head_to_head=h2h,
            )
            matchups.append(matchup)

        return matchups

    def _get_mock_injury_report(self, team_id: str) -> InjuryReport:
        """Generate mock injury report data for demonstration."""
        # Simulate some injuries based on team
        injuries = []

        # Add a mock injury for demonstration
        if "kc" in team_id.lower() or "sf" in team_id.lower():
            injuries.append(
                Injury(
                    player_id=f"{team_id}_player1",
                    player_name="Star Player",
                    team_id=team_id,
                    status=InjuryStatus.QUESTIONABLE,
                    injury_type="knee",
                    description="Knee sprain, questionable for game",
                    impact_score=0.4,
                )
            )

        return InjuryReport(
            team_id=team_id,
            team_name=team_id.split("_")[-1].upper(),
            injuries=injuries,
        )

    def close(self) -> None:
        """Close the HTTP session."""
        if self._session:
            self._session.close()
            self._session = None
