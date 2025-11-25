# MyParlai 🎰

An AI-powered sports Parlay picking bot that leverages real-time data for intelligent betting predictions.

## Features

- **AI-Powered Analysis**: Uses advanced factor analysis to evaluate matchups and generate picks with confidence ratings
- **Real-Time Data Integration**:
  - Matchup analysis with team statistics and records
  - Weather reports for outdoor games
  - Injury reports and player availability
  - Head-to-head historical records
  - Live betting odds
- **Multiple Sports Support**: NFL, NBA, MLB, NHL, NCAAF, NCAAB
- **Configurable Betting Modes**:
  - Safe mode: Conservative picks with higher confidence
  - Normal mode: Balanced approach
  - Aggressive mode: More legs, higher risk/reward

## Installation

```bash
# Clone the repository
git clone https://github.com/your-username/MyParlai.git
cd MyParlai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Or install from requirements
pip install -r requirements.txt
```

## Quick Start

```bash
# Generate an NFL parlay for today
python -m src.cli.main generate nfl

# Generate a 3-leg NBA parlay with $20 stake
python -m src.cli.main generate nba --legs 3 --stake 20

# Analyze a specific matchup
python -m src.cli.main analyze nfl KC SF --verbose

# List today's matchups
python -m src.cli.main matchups nfl
```

## Usage

### Generate Parlay

```bash
python -m src.cli.main generate <sport> [options]
```

Options:
- `--legs, -l`: Number of legs (default: 3)
- `--stake, -s`: Stake amount (default: $10)
- `--mode, -m`: Betting mode [safe|normal|aggressive]
- `--types, -t`: Bet types to include [spread|moneyline|over|under]

### Analyze Matchup

```bash
python -m src.cli.main analyze <sport> <team1> <team2> [--verbose]
```

### List Matchups

```bash
python -m src.cli.main matchups <sport> [--date YYYY-MM-DD]
```

## Example Output

```
🎰 AI Parlay - 2024-11-25 (3 legs)
   Stake: $10.00
   Odds: +595
   Potential Payout: $69.50
   Avg Confidence: 62.5%

   Legs:
   1. 🟢 KC -3.5 (-110) - high
   2. 🟢 BUF ML (-140) - high
   3. 🟡 OVER 48.5 (-110) - medium

📊 Win Probability: 18.2%
💰 Potential Profit: $59.50

📝 Analysis:
  Leg 1: KC -3.5
    Reasoning: Taking home team on spread: Home team (70.6%) significantly better record than away (64.7%); H2H record: Home 3-2 Away; Home field advantage for Kansas City Chiefs
    Key Factors:
      • Home team (70.6%) significantly better record than away (64.7%)
      • H2H record: Home 3-2 Away
      • Home field advantage for Kansas City Chiefs
```

## Project Structure

```
MyParlai/
├── src/
│   ├── models/          # Data models
│   │   ├── sport.py     # Sport types and configuration
│   │   ├── team.py      # Team and statistics
│   │   ├── player.py    # Player information
│   │   ├── matchup.py   # Game matchups
│   │   ├── weather.py   # Weather conditions
│   │   ├── injury.py    # Injury reports
│   │   └── parlay.py    # Parlay and betting
│   ├── services/        # Data fetching services
│   │   ├── sports_data.py   # Sports data API
│   │   ├── weather_service.py  # Weather API
│   │   └── odds_service.py  # Betting odds API
│   ├── analysis/        # Prediction engine
│   │   ├── factors.py   # Factor analysis
│   │   └── predictor.py # AI prediction
│   └── cli/            # Command-line interface
│       └── main.py
├── tests/              # Unit tests
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Configuration

Set the following environment variables for real API data:

```bash
# Sports data API
export SPORTS_API_KEY=your_api_key

# Weather API
export WEATHER_API_KEY=your_api_key

# Odds API
export ODDS_API_KEY=your_api_key
```

Without API keys, the bot uses realistic mock data for demonstration.

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=src

# Run linter
flake8 src tests

# Format code
black src tests
```

## Analysis Factors

The AI considers these factors when making predictions:

1. **Team Records**: Win/loss percentages and point differentials
2. **Head-to-Head**: Historical matchup records
3. **Injuries**: Impact of player absences on team performance
4. **Home Advantage**: Home field/court advantage adjustments
5. **Weather**: Impact on outdoor games (wind, temperature, precipitation)
6. **Recent Form**: Current winning/losing streaks
7. **Rest Days**: Back-to-back games and travel considerations

## Disclaimer

⚠️ **This is for entertainment purposes only.** Gambling involves risk and should be done responsibly. Past performance does not guarantee future results. Please gamble responsibly and within your means.

## License

MIT License
