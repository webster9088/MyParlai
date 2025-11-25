"""
Unit tests for the parlay calculation module.
"""
import unittest

from src.parlay import (
    BetSelection,
    Parlay,
    american_to_decimal,
    decimal_to_american,
    calculate_implied_probability,
    calculate_parlay_odds,
    calculate_payout,
    analyze_parlay,
    suggest_value_bets,
)


class TestOddsConversions(unittest.TestCase):
    """Test odds conversion functions."""

    def test_american_to_decimal_positive(self):
        """Test converting positive American odds to decimal."""
        # +150 should convert to 2.50
        self.assertAlmostEqual(american_to_decimal(150), 2.50, places=2)
        # +100 should convert to 2.00
        self.assertAlmostEqual(american_to_decimal(100), 2.00, places=2)
        # +200 should convert to 3.00
        self.assertAlmostEqual(american_to_decimal(200), 3.00, places=2)

    def test_american_to_decimal_negative(self):
        """Test converting negative American odds to decimal."""
        # -150 should convert to 1.67
        self.assertAlmostEqual(american_to_decimal(-150), 1.67, places=2)
        # -100 should convert to 2.00
        self.assertAlmostEqual(american_to_decimal(-100), 2.00, places=2)
        # -110 should convert to 1.91
        self.assertAlmostEqual(american_to_decimal(-110), 1.91, places=2)

    def test_decimal_to_american_favorite(self):
        """Test converting decimal odds to American for favorites."""
        # 1.50 decimal should be -200 American
        self.assertEqual(decimal_to_american(1.50), -200)
        # 1.67 decimal should be approximately -150 American
        result = decimal_to_american(1.67)
        self.assertTrue(-155 <= result <= -145)

    def test_decimal_to_american_underdog(self):
        """Test converting decimal odds to American for underdogs."""
        # 2.50 decimal should be +150 American
        self.assertEqual(decimal_to_american(2.50), 150)
        # 3.00 decimal should be +200 American
        self.assertEqual(decimal_to_american(3.00), 200)


class TestImpliedProbability(unittest.TestCase):
    """Test implied probability calculations."""

    def test_implied_probability_negative_odds(self):
        """Test implied probability for favorites."""
        # -150 odds = 60% implied probability
        prob = calculate_implied_probability(-150)
        self.assertAlmostEqual(prob, 0.60, places=2)

    def test_implied_probability_positive_odds(self):
        """Test implied probability for underdogs."""
        # +150 odds = 40% implied probability
        prob = calculate_implied_probability(150)
        self.assertAlmostEqual(prob, 0.40, places=2)

    def test_implied_probability_even_odds(self):
        """Test implied probability for even odds."""
        # +100 or -100 = 50% implied probability
        self.assertAlmostEqual(calculate_implied_probability(100), 0.50, places=2)
        self.assertAlmostEqual(calculate_implied_probability(-100), 0.50, places=2)


class TestBetSelection(unittest.TestCase):
    """Test BetSelection dataclass."""

    def test_bet_selection_str_h2h(self):
        """Test string representation for head-to-head bet."""
        selection = BetSelection(
            game_id="game1",
            game_description="Team A @ Team B",
            selection_name="Team A",
            market_type="h2h",
            odds=-150,
        )
        str_repr = str(selection)
        self.assertIn("Team A", str_repr)
        self.assertIn("h2h", str_repr)
        self.assertIn("-150", str_repr)

    def test_bet_selection_str_spread(self):
        """Test string representation for spread bet."""
        selection = BetSelection(
            game_id="game1",
            game_description="Team A @ Team B",
            selection_name="Team A",
            market_type="spread",
            odds=-110,
            point=-3.5,
        )
        str_repr = str(selection)
        self.assertIn("Team A", str_repr)
        self.assertIn("-3.5", str_repr)
        self.assertIn("-110", str_repr)


class TestParlay(unittest.TestCase):
    """Test Parlay class functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.parlay = Parlay()
        self.selection1 = BetSelection(
            game_id="game1",
            game_description="Team A @ Team B",
            selection_name="Team A",
            market_type="h2h",
            odds=-150,
        )
        self.selection2 = BetSelection(
            game_id="game2",
            game_description="Team C @ Team D",
            selection_name="Team C",
            market_type="h2h",
            odds=130,
        )

    def test_add_selection(self):
        """Test adding selections to parlay."""
        self.assertTrue(self.parlay.add_selection(self.selection1))
        self.assertEqual(len(self.parlay.selections), 1)

    def test_add_duplicate_game(self):
        """Test that same game cannot be added twice."""
        self.parlay.add_selection(self.selection1)
        duplicate = BetSelection(
            game_id="game1",  # Same game ID
            game_description="Team A @ Team B",
            selection_name="Team B",  # Different selection
            market_type="h2h",
            odds=130,
        )
        self.assertFalse(self.parlay.add_selection(duplicate))
        self.assertEqual(len(self.parlay.selections), 1)

    def test_remove_selection(self):
        """Test removing selections from parlay."""
        self.parlay.add_selection(self.selection1)
        self.parlay.add_selection(self.selection2)
        self.assertTrue(self.parlay.remove_selection(0))
        self.assertEqual(len(self.parlay.selections), 1)

    def test_remove_invalid_index(self):
        """Test removing with invalid index."""
        self.assertFalse(self.parlay.remove_selection(0))
        self.assertFalse(self.parlay.remove_selection(-1))

    def test_clear_parlay(self):
        """Test clearing all selections."""
        self.parlay.add_selection(self.selection1)
        self.parlay.add_selection(self.selection2)
        self.parlay.clear()
        self.assertEqual(len(self.parlay.selections), 0)

    def test_set_stake(self):
        """Test setting stake amount."""
        self.parlay.set_stake(100.0)
        self.assertEqual(self.parlay.stake, 100.0)

    def test_set_negative_stake(self):
        """Test that negative stake is not allowed."""
        self.parlay.set_stake(-50.0)
        self.assertEqual(self.parlay.stake, 0.0)


class TestParlayCalculations(unittest.TestCase):
    """Test parlay odds and payout calculations."""

    def setUp(self):
        """Set up test fixtures."""
        self.selection1 = BetSelection(
            game_id="game1",
            game_description="Team A @ Team B",
            selection_name="Team A",
            market_type="h2h",
            odds=-110,  # Decimal: 1.91
        )
        self.selection2 = BetSelection(
            game_id="game2",
            game_description="Team C @ Team D",
            selection_name="Team C",
            market_type="h2h",
            odds=-110,  # Decimal: 1.91
        )

    def test_calculate_parlay_odds_empty(self):
        """Test calculating odds for empty parlay."""
        result = calculate_parlay_odds([])
        self.assertEqual(result["decimal_odds"], 0)
        self.assertEqual(result["american_odds"], 0)

    def test_calculate_parlay_odds_single(self):
        """Test calculating odds for single selection."""
        result = calculate_parlay_odds([self.selection1])
        # Single -110 should be approximately 1.91 decimal
        self.assertAlmostEqual(result["decimal_odds"], 1.91, places=1)

    def test_calculate_parlay_odds_two_legs(self):
        """Test calculating odds for two-leg parlay."""
        result = calculate_parlay_odds([self.selection1, self.selection2])
        # Two -110 legs: 1.91 * 1.91 ≈ 3.65
        self.assertAlmostEqual(result["decimal_odds"], 3.65, places=1)
        # Combined American odds should be around +265
        self.assertTrue(260 <= result["american_odds"] <= 270)

    def test_calculate_payout(self):
        """Test calculating payout for parlay."""
        stake = 100.0
        result = calculate_payout(stake, [self.selection1, self.selection2])
        # $100 at ~3.65 odds = ~$365 total payout
        self.assertGreater(result["total_payout"], 350)
        self.assertLess(result["total_payout"], 380)
        # Profit should be payout - stake
        self.assertAlmostEqual(
            result["profit"], result["total_payout"] - stake, places=2
        )

    def test_calculate_payout_zero_stake(self):
        """Test payout with zero stake."""
        result = calculate_payout(0, [self.selection1])
        self.assertEqual(result["total_payout"], 0.0)
        self.assertEqual(result["profit"], 0.0)

    def test_calculate_payout_no_selections(self):
        """Test payout with no selections."""
        result = calculate_payout(100, [])
        self.assertEqual(result["total_payout"], 0.0)


class TestAnalyzeParlay(unittest.TestCase):
    """Test parlay analysis function."""

    def test_analyze_parlay(self):
        """Test comprehensive parlay analysis."""
        parlay = Parlay()
        parlay.add_selection(
            BetSelection(
                game_id="game1",
                game_description="Team A @ Team B",
                selection_name="Team A",
                market_type="h2h",
                odds=-150,
            )
        )
        parlay.add_selection(
            BetSelection(
                game_id="game2",
                game_description="Team C @ Team D",
                selection_name="Team C",
                market_type="h2h",
                odds=130,
            )
        )
        parlay.set_stake(50.0)

        analysis = analyze_parlay(parlay)

        self.assertEqual(analysis["num_legs"], 2)
        self.assertEqual(analysis["stake"], 50.0)
        self.assertIn("combined_decimal_odds", analysis)
        self.assertIn("combined_american_odds", analysis)
        self.assertIn("potential_payout", analysis)
        self.assertGreater(analysis["potential_payout"], 50)


class TestValueBetSuggestions(unittest.TestCase):
    """Test value bet suggestion function."""

    def test_suggest_value_bets(self):
        """Test generating value bet suggestions."""
        odds_data = [
            {
                "id": "game1",
                "home_team": "Team A",
                "away_team": "Team B",
                "bookmakers": [
                    {
                        "key": "test",
                        "markets": [
                            {
                                "key": "h2h",
                                "outcomes": [
                                    {"name": "Team A", "price": -150},
                                    {"name": "Team B", "price": 130},
                                ],
                            }
                        ],
                    }
                ],
            }
        ]

        suggestions = suggest_value_bets(odds_data)
        self.assertGreater(len(suggestions), 0)

        # Verify suggestions are sorted by implied probability (descending)
        for i in range(len(suggestions) - 1):
            self.assertGreaterEqual(
                suggestions[i]["implied_probability"],
                suggestions[i + 1]["implied_probability"],
            )

    def test_suggest_value_bets_empty(self):
        """Test suggestions with empty data."""
        suggestions = suggest_value_bets([])
        self.assertEqual(len(suggestions), 0)


if __name__ == "__main__":
    unittest.main()
