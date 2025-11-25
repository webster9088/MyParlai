"""Main CLI entry point for MyParlai."""

import argparse
import sys
from datetime import datetime
from typing import List, Optional

from src.models.parlay import BetType
from src.services.sports_data import SportsDataService
from src.services.weather_service import WeatherService
from src.analysis.predictor import ParlayPredictor


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="parlai",
        description="🎰 MyParlai - AI-Powered Sports Parlay Picker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  parlai generate nfl                  Generate NFL parlay for today
  parlai generate nba --legs 3         Generate 3-leg NBA parlay
  parlai analyze nfl KC SF             Analyze Chiefs vs 49ers matchup
  parlai matchups nfl                  List today's NFL matchups
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Generate parlay command
    gen_parser = subparsers.add_parser("generate", help="Generate a parlay")
    gen_parser.add_argument("sport", help="Sport to generate parlay for")
    gen_parser.add_argument(
        "--legs", "-l", type=int, default=3, help="Number of legs (default: 3)"
    )
    gen_parser.add_argument(
        "--stake", "-s", type=float, default=10.0, help="Stake amount (default: $10)"
    )
    gen_parser.add_argument(
        "--mode",
        "-m",
        choices=["safe", "normal", "aggressive"],
        default="normal",
        help="Betting mode (default: normal)",
    )
    gen_parser.add_argument(
        "--types",
        "-t",
        nargs="+",
        choices=["spread", "moneyline", "over", "under"],
        help="Bet types to include",
    )

    # Analyze matchup command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a specific matchup")
    analyze_parser.add_argument("sport", help="Sport")
    analyze_parser.add_argument("team1", help="First team abbreviation")
    analyze_parser.add_argument("team2", help="Second team abbreviation")
    analyze_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed analysis"
    )

    # List matchups command
    matchups_parser = subparsers.add_parser("matchups", help="List available matchups")
    matchups_parser.add_argument("sport", help="Sport to list matchups for")
    matchups_parser.add_argument(
        "--date", "-d", help="Date for matchups (YYYY-MM-DD)"
    )

    # Info command
    subparsers.add_parser("info", help="Show program info")

    return parser


def cmd_generate(args: argparse.Namespace) -> int:
    """Handle generate command."""
    print(f"\n🎰 Generating {args.sport.upper()} parlay...")
    print("=" * 50)

    # Initialize services
    sports_service = SportsDataService()
    weather_service = WeatherService()
    predictor = ParlayPredictor()

    try:
        # Get matchups
        matchups = sports_service.get_matchups(args.sport)

        if not matchups:
            print(f"❌ No matchups found for {args.sport.upper()} today")
            return 1

        # Add weather data
        for matchup in matchups:
            weather = weather_service.get_weather(
                location=matchup.home_team.city,
                game_time=matchup.game_time,
                venue=matchup.venue,
                sport=args.sport,
            )
            matchup.weather = weather

        # Determine bet types
        bet_types = None
        if args.types:
            type_map = {
                "spread": BetType.SPREAD,
                "moneyline": BetType.MONEYLINE,
                "over": BetType.OVER,
                "under": BetType.UNDER,
            }
            bet_types = [type_map[t] for t in args.types]

        # Generate parlay based on mode
        if args.mode == "safe":
            parlay = predictor.generate_safe_parlay(matchups, stake=args.stake)
        elif args.mode == "aggressive":
            parlay = predictor.generate_aggressive_parlay(matchups, stake=args.stake)
        else:
            parlay = predictor.generate_parlay(
                matchups=matchups,
                num_legs=args.legs,
                bet_types=bet_types,
                stake=args.stake,
            )

        # Display the parlay
        print(parlay.get_summary())
        print("\n" + "=" * 50)
        print(f"📊 Win Probability: {parlay.implied_win_probability:.1%}")
        print(f"💰 Potential Profit: ${parlay.potential_profit:.2f}")

        # Show reasoning for each leg
        print("\n📝 Analysis:")
        for i, leg in enumerate(parlay.legs, 1):
            print(f"\n  Leg {i}: {leg.pick}")
            print(f"    Reasoning: {leg.reasoning}")
            if leg.key_factors:
                print("    Key Factors:")
                for factor in leg.key_factors[:3]:
                    print(f"      • {factor}")

    finally:
        sports_service.close()
        weather_service.close()

    return 0


def cmd_analyze(args: argparse.Namespace) -> int:
    """Handle analyze command."""
    print(f"\n🔍 Analyzing {args.team1} vs {args.team2} ({args.sport.upper()})...")
    print("=" * 50)

    sports_service = SportsDataService()
    weather_service = WeatherService()
    predictor = ParlayPredictor()

    try:
        # Get matchups and find the one we want
        matchups = sports_service.get_matchups(args.sport)

        target_matchup = None
        for matchup in matchups:
            if (
                args.team1.upper() in matchup.home_team.abbreviation
                or args.team1.upper() in matchup.away_team.abbreviation
            ) and (
                args.team2.upper() in matchup.home_team.abbreviation
                or args.team2.upper() in matchup.away_team.abbreviation
            ):
                target_matchup = matchup
                break

        if not target_matchup:
            print(f"❌ Matchup not found: {args.team1} vs {args.team2}")
            return 1

        # Add weather
        weather = weather_service.get_weather(
            location=target_matchup.home_team.city,
            game_time=target_matchup.game_time,
            venue=target_matchup.venue,
            sport=args.sport,
        )
        target_matchup.weather = weather

        # Analyze
        analysis = predictor.analyze_matchup(target_matchup)

        print(f"\n📋 {target_matchup.get_summary()}")
        print("\n📊 Odds:")
        print(f"   Spread: {target_matchup.odds.spread:+.1f}")
        print(f"   ML Home: {target_matchup.odds.moneyline_home:+d}")
        print(f"   ML Away: {target_matchup.odds.moneyline_away:+d}")
        print(f"   O/U: {target_matchup.odds.over_under}")

        print("\n🌤️ Weather:")
        if weather.is_dome:
            print("   Indoor game - no weather impact")
        else:
            print(f"   {weather.conditions}, {weather.temperature}°F")
            print(f"   Wind: {weather.wind_speed} mph {weather.wind_direction}")
            print(f"   Precipitation: {weather.precipitation_chance}%")

        print("\n📈 Analysis Scores:")
        print(f"   Home: {analysis.home_score:.3f}")
        print(f"   Away: {analysis.away_score:.3f}")
        print(f"   Confidence: {analysis.confidence:.1%}")

        print("\n🎯 Predictions:")
        spread_pick = predictor.predict_spread(target_matchup, analysis)
        ml_pick = predictor.predict_moneyline(target_matchup, analysis)
        total_pick = predictor.predict_total(target_matchup, analysis)

        print(f"   Spread: {spread_pick.pick} ({spread_pick.confidence.value})")
        print(f"   Moneyline: {ml_pick.pick} ({ml_pick.confidence.value})")
        print(f"   Total: {total_pick.pick} ({total_pick.confidence.value})")

        if args.verbose:
            print("\n📊 Factor Details:")
            for factor in analysis.factors:
                print(f"   {factor.name}: {factor.value:+.3f} × {factor.weight:.2f}")
                print(f"      {factor.description}")

    finally:
        sports_service.close()
        weather_service.close()

    return 0


def cmd_matchups(args: argparse.Namespace) -> int:
    """Handle matchups command."""
    date = datetime.utcnow()
    if args.date:
        date = datetime.strptime(args.date, "%Y-%m-%d")

    print(f"\n📅 {args.sport.upper()} Matchups for {date.strftime('%Y-%m-%d')}")
    print("=" * 50)

    sports_service = SportsDataService()

    try:
        matchups = sports_service.get_matchups(args.sport, date=date)

        if not matchups:
            print(f"No matchups found for {args.sport.upper()}")
            return 0

        for i, matchup in enumerate(matchups, 1):
            print(f"\n{i}. {matchup.get_summary()}")
            print(f"   Spread: {matchup.odds.spread:+.1f}")
            print(f"   O/U: {matchup.odds.over_under}")

            # Show injury info if present
            if matchup.home_injuries and matchup.home_injuries.total_injuries > 0:
                print(
                    f"   🏥 {matchup.home_team.abbreviation}: "
                    f"{matchup.home_injuries.total_injuries} injuries"
                )
            if matchup.away_injuries and matchup.away_injuries.total_injuries > 0:
                print(
                    f"   🏥 {matchup.away_team.abbreviation}: "
                    f"{matchup.away_injuries.total_injuries} injuries"
                )

    finally:
        sports_service.close()

    return 0


def cmd_info(args: argparse.Namespace) -> int:
    """Handle info command."""
    print("""
🎰 MyParlai - AI-Powered Sports Parlay Picker
==============================================

Version: 0.1.0

Features:
  • AI-powered matchup analysis
  • Real-time injury reports
  • Weather impact analysis
  • Head-to-head records
  • Confidence-based picks

Supported Sports:
  • NFL (National Football League)
  • NBA (National Basketball Association)
  • MLB (Major League Baseball)
  • NHL (National Hockey League)
  • NCAAF (College Football)
  • NCAAB (College Basketball)

For more information, run: parlai --help
    """)
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point for the CLI.

    Args:
        argv: Command line arguments. Defaults to sys.argv[1:].

    Returns:
        Exit code (0 for success, non-zero for error).
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    commands = {
        "generate": cmd_generate,
        "analyze": cmd_analyze,
        "matchups": cmd_matchups,
        "info": cmd_info,
    }

    handler = commands.get(args.command)
    if handler:
        return handler(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
