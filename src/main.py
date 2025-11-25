#!/usr/bin/env python3
"""
Sports Parlay Picking Program - Main CLI Application.

This program allows users to view live sports odds, build parlays,
and calculate potential payouts.

Required API Keys:
    ODDS_API_KEY: For live sports data from The Odds API.
                  Get your free key at: https://the-odds-api.com/
"""
import sys
from typing import Optional

from src.sports_data import (
    SportsDataClient,
    APIKeyMissingError,
    get_sample_odds_data,
    get_sample_sports_data,
)
from src.parlay import (
    BetSelection,
    Parlay,
    format_parlay_summary,
    suggest_value_bets,
)


class ParlayPicker:
    """Main application class for the parlay picking program."""

    def __init__(self, use_sample_data: bool = False):
        """
        Initialize the parlay picker.

        Args:
            use_sample_data: If True, use sample data instead of live API.
        """
        self.client = SportsDataClient()
        self.use_sample_data = use_sample_data
        self.current_parlay = Parlay()
        self.cached_odds: list = []
        self.cached_sports: list = []

    def load_sports(self) -> list:
        """Load available sports list."""
        if self.use_sample_data:
            self.cached_sports = get_sample_sports_data()
        else:
            self.cached_sports = self.client.get_sports()
        return self.cached_sports

    def load_odds(self, sport: str = "upcoming") -> list:
        """
        Load odds data for a sport.

        Args:
            sport: Sport key or 'upcoming' for all upcoming games.
        """
        if self.use_sample_data:
            self.cached_odds = get_sample_odds_data()
        else:
            self.cached_odds = self.client.get_odds(sport)
        return self.cached_odds

    def display_sports(self) -> None:
        """Display available sports."""
        sports = self.load_sports()
        if not sports:
            print("No sports data available.")
            return

        print("\n" + "=" * 50)
        print("AVAILABLE SPORTS")
        print("=" * 50)

        for i, sport in enumerate(sports, 1):
            status = "[ACTIVE]" if sport.get("active") else "[INACTIVE]"
            print(
                f"{i}. {sport.get('title', 'Unknown')} "
                f"({sport.get('key', 'unknown')}) {status}"
            )

        print("=" * 50 + "\n")

    def display_odds(self, sport: str = "upcoming") -> None:
        """
        Display odds for games.

        Args:
            sport: Sport key to display odds for.
        """
        odds = self.load_odds(sport)
        if not odds:
            print("No odds data available.")
            return

        print("\n" + "=" * 60)
        print(f"ODDS DATA - {sport.upper()}")
        print("=" * 60)

        for i, game in enumerate(odds, 1):
            home = game.get("home_team", "Unknown")
            away = game.get("away_team", "Unknown")
            sport_title = game.get("sport_title", "")
            time_str = game.get("commence_time", "TBD")

            print(f"\n[{i}] {sport_title}: {away} @ {home}")
            print(f"    Game ID: {game.get('id', 'N/A')}")
            print(f"    Start Time: {time_str}")

            bookmakers = game.get("bookmakers", [])
            if bookmakers:
                book = bookmakers[0]
                print(f"    Odds from: {book.get('title', 'Unknown')}")

                for market in book.get("markets", []):
                    market_key = market.get("key", "")
                    print(f"      {market_key.upper()}:")

                    for outcome in market.get("outcomes", []):
                        name = outcome.get("name", "Unknown")
                        price = outcome.get("price", 0)
                        point = outcome.get("point")

                        price_str = f"+{price}" if price > 0 else str(price)
                        if point is not None:
                            print(f"        - {name} ({point:+.1f}): {price_str}")
                        else:
                            print(f"        - {name}: {price_str}")

        print("\n" + "=" * 60 + "\n")

    def display_suggestions(self) -> None:
        """Display value bet suggestions."""
        if not self.cached_odds:
            print("Please load odds data first (option 2).")
            return

        suggestions = suggest_value_bets(self.cached_odds)

        print("\n" + "=" * 60)
        print("VALUE BET SUGGESTIONS")
        print("=" * 60)
        print("(Picks sorted by implied probability - higher = safer)\n")

        for i, sugg in enumerate(suggestions[:10], 1):
            sel = sugg["selection"]
            prob = sugg["implied_probability"]
            print(f"{i}. {sel.game_description}")
            print(f"   Pick: {sel}")
            print(f"   Implied Win Probability: {prob:.1f}%")
            print()

        print("=" * 60 + "\n")

    def add_to_parlay_interactive(self) -> None:
        """Interactive mode to add selections to the parlay."""
        if not self.cached_odds:
            print("Please load odds data first (option 2).")
            return

        print("\nEnter game number to select from (0 to cancel): ", end="")
        try:
            game_num = int(input())
            if game_num == 0:
                return
            if game_num < 1 or game_num > len(self.cached_odds):
                print("Invalid game number.")
                return
        except ValueError:
            print("Invalid input.")
            return

        game = self.cached_odds[game_num - 1]
        bookmakers = game.get("bookmakers", [])
        if not bookmakers:
            print("No odds available for this game.")
            return

        book = bookmakers[0]
        markets = book.get("markets", [])

        print("\nAvailable markets:")
        all_outcomes = []
        idx = 1
        for market in markets:
            market_key = market.get("key", "")
            for outcome in market.get("outcomes", []):
                name = outcome.get("name", "Unknown")
                price = outcome.get("price", 0)
                point = outcome.get("point")

                price_str = f"+{price}" if price > 0 else str(price)
                if point is not None:
                    desc = f"{name} ({market_key} {point:+.1f})"
                else:
                    desc = f"{name} ({market_key})"

                print(f"  {idx}. {desc}: {price_str}")
                all_outcomes.append(
                    {
                        "market_key": market_key,
                        "outcome": outcome,
                    }
                )
                idx += 1

        print("\nEnter selection number (0 to cancel): ", end="")
        try:
            sel_num = int(input())
            if sel_num == 0:
                return
            if sel_num < 1 or sel_num > len(all_outcomes):
                print("Invalid selection number.")
                return
        except ValueError:
            print("Invalid input.")
            return

        chosen = all_outcomes[sel_num - 1]
        outcome = chosen["outcome"]

        selection = BetSelection(
            game_id=game.get("id", ""),
            game_description=f"{game.get('away_team')} @ {game.get('home_team')}",
            selection_name=outcome.get("name", ""),
            market_type=chosen["market_key"],
            odds=outcome.get("price", 0),
            point=outcome.get("point"),
        )

        if self.current_parlay.add_selection(selection):
            print(f"\n✓ Added to parlay: {selection}")
            print(f"  Current parlay has {len(self.current_parlay.selections)} leg(s)")
        else:
            print("Could not add selection to parlay.")

    def set_stake_interactive(self) -> None:
        """Interactive mode to set the stake."""
        print("\nEnter stake amount: $", end="")
        try:
            stake = float(input())
            if stake <= 0:
                print("Stake must be greater than 0.")
                return
            self.current_parlay.set_stake(stake)
            print(f"✓ Stake set to ${stake:.2f}")
        except ValueError:
            print("Invalid amount.")

    def show_parlay(self) -> None:
        """Display current parlay summary."""
        print(format_parlay_summary(self.current_parlay))

    def clear_parlay(self) -> None:
        """Clear the current parlay."""
        self.current_parlay.clear()
        print("✓ Parlay cleared.")

    def run(self) -> None:
        """Run the main application loop."""
        print("\n" + "=" * 50)
        print("  SPORTS PARLAY PICKER")
        print("  Build your parlays with live odds data!")
        print("=" * 50)

        if self.use_sample_data:
            print("\n[Running with sample data - no API key required]")

        while True:
            print("\n--- MAIN MENU ---")
            print("1. View Available Sports")
            print("2. View Odds (loads data)")
            print("3. View Value Bet Suggestions")
            print("4. Add Selection to Parlay")
            print("5. Set Stake Amount")
            print("6. View Current Parlay")
            print("7. Clear Parlay")
            print("8. Exit")
            print()

            choice = input("Enter choice (1-8): ").strip()

            if choice == "1":
                self.display_sports()
            elif choice == "2":
                sport = input(
                    "Enter sport key (or press Enter for 'upcoming'): "
                ).strip()
                self.display_odds(sport if sport else "upcoming")
            elif choice == "3":
                self.display_suggestions()
            elif choice == "4":
                self.add_to_parlay_interactive()
            elif choice == "5":
                self.set_stake_interactive()
            elif choice == "6":
                self.show_parlay()
            elif choice == "7":
                self.clear_parlay()
            elif choice == "8":
                print("\nGoodbye! Good luck with your bets! 🎲")
                break
            else:
                print("Invalid choice. Please enter 1-8.")


def main(use_sample: bool = True) -> None:
    """
    Main entry point for the application.

    Args:
        use_sample: If True, use sample data (default for demo).
    """
    # Validate API key is available when using live data
    if not use_sample:
        client = SportsDataClient()
        if not client.has_api_key():
            print("\n" + "=" * 60)
            print("ERROR: API Key Required for Live Data")
            print("=" * 60)
            print("\nTo use live sports data, you need an API key from The Odds API.")
            print("\nSetup instructions:")
            print("  1. Get your free API key at: https://the-odds-api.com/")
            print("  2. Set the environment variable:")
            print("     export ODDS_API_KEY=your_api_key_here")
            print("  3. Or create a .env file with: ODDS_API_KEY=your_api_key_here")
            print("\nAlternatively, run without --live flag to use sample data:")
            print("  python -m src.main")
            print("=" * 60 + "\n")
            sys.exit(1)

    picker = ParlayPicker(use_sample_data=use_sample)
    picker.run()


if __name__ == "__main__":
    # Check if --live flag is passed for live API data
    use_live = "--live" in sys.argv
    main(use_sample=not use_live)
