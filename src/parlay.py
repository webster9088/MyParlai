"""
Parlay Calculator and Picker Module.

This module provides functionality for calculating parlay odds,
potential payouts, and managing parlay selections.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BetSelection:
    """Represents a single bet selection in a parlay."""

    game_id: str
    game_description: str
    selection_name: str
    market_type: str  # h2h, spread, total
    odds: int  # American odds
    point: Optional[float] = None  # For spreads and totals

    def __str__(self) -> str:
        """Return string representation of the bet selection."""
        odds_str = f"+{self.odds}" if self.odds > 0 else str(self.odds)
        if self.point is not None:
            return (
                f"{self.selection_name} ({self.market_type} {self.point:+.1f}) "
                f"@ {odds_str}"
            )
        return f"{self.selection_name} ({self.market_type}) @ {odds_str}"


@dataclass
class Parlay:
    """Represents a parlay bet with multiple selections."""

    selections: list = field(default_factory=list)
    stake: float = 0.0

    def add_selection(self, selection: BetSelection) -> bool:
        """
        Add a selection to the parlay.

        Args:
            selection: The bet selection to add.

        Returns:
            True if selection was added, False if game already in parlay.
        """
        # Check if game is already in parlay (can't bet same game twice)
        for existing in self.selections:
            if existing.game_id == selection.game_id:
                print(
                    f"Warning: Game {selection.game_id} already in parlay. "
                    "Cannot add same game twice."
                )
                return False
        self.selections.append(selection)
        return True

    def remove_selection(self, index: int) -> bool:
        """
        Remove a selection from the parlay by index.

        Args:
            index: Index of the selection to remove.

        Returns:
            True if selection was removed, False if index is invalid.
        """
        if 0 <= index < len(self.selections):
            self.selections.pop(index)
            return True
        return False

    def clear(self) -> None:
        """Clear all selections from the parlay."""
        self.selections.clear()

    def set_stake(self, stake: float) -> None:
        """
        Set the stake amount for the parlay.

        Args:
            stake: Amount to wager.
        """
        self.stake = max(0.0, stake)


def american_to_decimal(american_odds: int) -> float:
    """
    Convert American odds to decimal odds.

    Args:
        american_odds: Odds in American format (e.g., -110, +150)

    Returns:
        Odds in decimal format.
    """
    if american_odds > 0:
        return (american_odds / 100) + 1
    return (100 / abs(american_odds)) + 1


def decimal_to_american(decimal_odds: float) -> int:
    """
    Convert decimal odds to American odds.

    Args:
        decimal_odds: Odds in decimal format.

    Returns:
        Odds in American format.
    """
    if decimal_odds >= 2.0:
        return int((decimal_odds - 1) * 100)
    return int(-100 / (decimal_odds - 1))


def calculate_implied_probability(american_odds: int) -> float:
    """
    Calculate implied probability from American odds.

    Args:
        american_odds: Odds in American format.

    Returns:
        Implied probability as a decimal (0-1).
    """
    if american_odds > 0:
        return 100 / (american_odds + 100)
    return abs(american_odds) / (abs(american_odds) + 100)


def calculate_parlay_odds(selections: list) -> dict:
    """
    Calculate combined odds and probability for a parlay.

    Args:
        selections: List of BetSelection objects.

    Returns:
        Dictionary with combined decimal odds, American odds,
        and implied probability.
    """
    if not selections:
        return {"decimal_odds": 0, "american_odds": 0, "implied_probability": 0}

    combined_decimal = 1.0
    combined_probability = 1.0

    for selection in selections:
        decimal_odds = american_to_decimal(selection.odds)
        combined_decimal *= decimal_odds
        combined_probability *= calculate_implied_probability(selection.odds)

    combined_american = decimal_to_american(combined_decimal)

    return {
        "decimal_odds": round(combined_decimal, 2),
        "american_odds": combined_american,
        "implied_probability": round(combined_probability * 100, 2),
    }


def calculate_payout(stake: float, selections: list) -> dict:
    """
    Calculate potential payout for a parlay.

    Args:
        stake: Amount wagered.
        selections: List of BetSelection objects.

    Returns:
        Dictionary with total payout and profit.
    """
    if not selections or stake <= 0:
        return {"total_payout": 0.0, "profit": 0.0}

    odds_info = calculate_parlay_odds(selections)
    total_payout = stake * odds_info["decimal_odds"]
    profit = total_payout - stake

    return {
        "total_payout": round(total_payout, 2),
        "profit": round(profit, 2),
    }


def analyze_parlay(parlay: Parlay) -> dict:
    """
    Analyze a parlay bet and return detailed information.

    Args:
        parlay: Parlay object to analyze.

    Returns:
        Dictionary with comprehensive parlay analysis.
    """
    odds_info = calculate_parlay_odds(parlay.selections)
    payout_info = calculate_payout(parlay.stake, parlay.selections)

    return {
        "num_legs": len(parlay.selections),
        "stake": parlay.stake,
        "combined_decimal_odds": odds_info["decimal_odds"],
        "combined_american_odds": odds_info["american_odds"],
        "implied_probability_percent": odds_info["implied_probability"],
        "potential_payout": payout_info["total_payout"],
        "potential_profit": payout_info["profit"],
        "selections": [str(s) for s in parlay.selections],
    }


def format_parlay_summary(parlay: Parlay) -> str:
    """
    Format a parlay into a readable summary string.

    Args:
        parlay: Parlay object to summarize.

    Returns:
        Formatted string summary of the parlay.
    """
    if not parlay.selections:
        return "No selections in parlay."

    analysis = analyze_parlay(parlay)

    lines = [
        "=" * 50,
        "PARLAY SUMMARY",
        "=" * 50,
        f"Number of Legs: {analysis['num_legs']}",
        "",
        "Selections:",
    ]

    for i, sel_str in enumerate(analysis["selections"], 1):
        lines.append(f"  {i}. {sel_str}")

    lines.extend(
        [
            "",
            f"Combined Odds: {analysis['combined_american_odds']:+d} "
            f"(Decimal: {analysis['combined_decimal_odds']})",
            f"Implied Win Probability: {analysis['implied_probability_percent']:.2f}%",
            "",
            f"Stake: ${analysis['stake']:.2f}",
            f"Potential Payout: ${analysis['potential_payout']:.2f}",
            f"Potential Profit: ${analysis['potential_profit']:.2f}",
            "=" * 50,
        ]
    )

    return "\n".join(lines)


def suggest_value_bets(odds_data: list, min_implied_prob: float = 0.3) -> list:
    """
    Suggest potential value bets based on odds data.

    This is a simple strategy that looks for underdogs with reasonable
    implied probabilities that could provide value in parlays.

    Args:
        odds_data: List of games with odds from API.
        min_implied_prob: Minimum implied probability (0-1) for suggestions.

    Returns:
        List of suggested BetSelection objects.
    """
    suggestions = []

    for game in odds_data:
        game_id = game.get("id", "")
        home_team = game.get("home_team", "")
        away_team = game.get("away_team", "")
        game_desc = f"{away_team} @ {home_team}"

        bookmakers = game.get("bookmakers", [])
        if not bookmakers:
            continue

        # Use first bookmaker's odds
        bookmaker = bookmakers[0]
        for market in bookmaker.get("markets", []):
            market_key = market.get("key", "")

            for outcome in market.get("outcomes", []):
                odds = outcome.get("price", 0)
                if odds == 0:
                    continue

                implied_prob = calculate_implied_probability(odds)

                # Suggest selections with reasonable probability
                if implied_prob >= min_implied_prob:
                    selection = BetSelection(
                        game_id=game_id,
                        game_description=game_desc,
                        selection_name=outcome.get("name", ""),
                        market_type=market_key,
                        odds=odds,
                        point=outcome.get("point"),
                    )
                    suggestions.append(
                        {
                            "selection": selection,
                            "implied_probability": round(implied_prob * 100, 2),
                        }
                    )

    # Sort by implied probability (higher = safer picks)
    suggestions.sort(key=lambda x: x["implied_probability"], reverse=True)

    return suggestions
