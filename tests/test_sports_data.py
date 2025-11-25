"""
Unit tests for the sports data module.
"""
import unittest
from unittest.mock import patch, MagicMock

import requests

from src.sports_data import (
    SportsDataClient,
    APIKeyMissingError,
    ODDS_API_KEY_ENV,
    get_sample_odds_data,
    get_sample_sports_data,
)


class TestSportsDataClient(unittest.TestCase):
    """Test SportsDataClient class."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = SportsDataClient(api_key="test_key")

    def test_init_with_api_key(self):
        """Test initialization with API key."""
        client = SportsDataClient(api_key="my_api_key")
        self.assertEqual(client.api_key, "my_api_key")

    @patch.dict("os.environ", {"ODDS_API_KEY": "env_key"})
    def test_init_from_env(self):
        """Test initialization from environment variable."""
        client = SportsDataClient()
        self.assertEqual(client.api_key, "env_key")

    def test_has_api_key_true(self):
        """Test has_api_key returns True when key is set."""
        self.assertTrue(self.client.has_api_key())

    def test_has_api_key_false(self):
        """Test has_api_key returns False when key is empty."""
        client = SportsDataClient(api_key="")
        self.assertFalse(client.has_api_key())

    def test_validate_api_key_success(self):
        """Test validate_api_key succeeds with valid key."""
        # Should not raise
        self.client.validate_api_key()

    def test_validate_api_key_missing(self):
        """Test validate_api_key raises APIKeyMissingError when key is empty."""
        client = SportsDataClient(api_key="")
        with self.assertRaises(APIKeyMissingError) as context:
            client.validate_api_key()
        self.assertIn(ODDS_API_KEY_ENV, str(context.exception))
        self.assertIn("https://the-odds-api.com/", str(context.exception))

    def test_get_sports_without_api_key(self):
        """Test get_sports raises error without API key."""
        client = SportsDataClient(api_key="")
        with self.assertRaises(APIKeyMissingError):
            client.get_sports()

    def test_get_odds_without_api_key(self):
        """Test get_odds raises error without API key."""
        client = SportsDataClient(api_key="")
        with self.assertRaises(APIKeyMissingError):
            client.get_odds()

    def test_get_scores_without_api_key(self):
        """Test get_scores raises error without API key."""
        client = SportsDataClient(api_key="")
        with self.assertRaises(APIKeyMissingError):
            client.get_scores(sport="nfl")

    def test_get_sports_success(self):
        """Test successful sports fetch."""
        with patch.object(self.client.session, "get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = [{"key": "nfl", "title": "NFL"}]
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            result = self.client.get_sports()

            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["key"], "nfl")
            mock_get.assert_called_once()

    def test_get_sports_error(self):
        """Test handling API error."""
        with patch.object(self.client.session, "get") as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException("API Error")

            result = self.client.get_sports()

            self.assertEqual(result, [])

    def test_get_odds_success(self):
        """Test successful odds fetch."""
        with patch.object(self.client.session, "get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = [
                {"id": "game1", "home_team": "Team A"}
            ]
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            result = self.client.get_odds(sport="americanfootball_nfl")

            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["id"], "game1")

    def test_get_odds_with_params(self):
        """Test odds fetch with custom parameters."""
        with patch.object(self.client.session, "get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = []
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            self.client.get_odds(
                sport="basketball_nba",
                regions="us,uk",
                markets="h2h",
                odds_format="decimal",
            )

            call_args = mock_get.call_args
            params = call_args[1]["params"]
            self.assertEqual(params["regions"], "us,uk")
            self.assertEqual(params["markets"], "h2h")
            self.assertEqual(params["oddsFormat"], "decimal")

    def test_get_scores_success(self):
        """Test successful scores fetch."""
        with patch.object(self.client.session, "get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = [
                {"id": "game1", "scores": [{"name": "Team A", "score": "21"}]}
            ]
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            result = self.client.get_scores(sport="americanfootball_nfl")

            self.assertEqual(len(result), 1)
            self.assertIn("scores", result[0])


class TestSampleData(unittest.TestCase):
    """Test sample data functions."""

    def test_get_sample_odds_data(self):
        """Test sample odds data structure."""
        data = get_sample_odds_data()

        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

        # Check first game structure
        game = data[0]
        self.assertIn("id", game)
        self.assertIn("sport_key", game)
        self.assertIn("home_team", game)
        self.assertIn("away_team", game)
        self.assertIn("bookmakers", game)

        # Check bookmaker structure
        bookmaker = game["bookmakers"][0]
        self.assertIn("key", bookmaker)
        self.assertIn("markets", bookmaker)

        # Check market structure
        market = bookmaker["markets"][0]
        self.assertIn("key", market)
        self.assertIn("outcomes", market)

    def test_get_sample_sports_data(self):
        """Test sample sports data structure."""
        data = get_sample_sports_data()

        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

        # Check sport structure
        sport = data[0]
        self.assertIn("key", sport)
        self.assertIn("title", sport)
        self.assertIn("group", sport)
        self.assertIn("active", sport)

    def test_sample_data_has_variety(self):
        """Test that sample data has different sports."""
        odds_data = get_sample_odds_data()
        sports = set(game["sport_key"] for game in odds_data)

        # Should have at least 2 different sports
        self.assertGreaterEqual(len(sports), 2)


if __name__ == "__main__":
    unittest.main()
