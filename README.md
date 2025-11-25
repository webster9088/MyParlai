# MyParlai - Sports Parlay Picking Program

Rolling dice and hoping for the best 🎲

A Python application for building sports parlays with live odds data.

## Features

- **Live Sports Data**: Fetch real-time odds from The Odds API
- **Parlay Builder**: Build multi-leg parlays from available games
- **Odds Calculator**: Automatic calculation of combined odds and potential payouts
- **Value Bet Suggestions**: Get suggestions for value picks based on implied probabilities
- **Multiple Sports**: Support for NFL, NBA, NHL, MLB, Soccer, and more

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/webster9088/MyParlai.git
   cd MyParlai
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. (Optional) Set up API key for live data:
   ```bash
   export ODDS_API_KEY=your_api_key_here
   ```
   
   Get your free API key at [The Odds API](https://the-odds-api.com/)

## Usage

### Run with Sample Data (No API key required)

```bash
python -m src.main
```

### Run with Live Data

```bash
python -m src.main --live
```

### Interactive Menu

The program provides an interactive menu:

1. **View Available Sports** - List all sports with available odds
2. **View Odds** - Display current odds for games
3. **View Value Bet Suggestions** - Get suggested picks
4. **Add Selection to Parlay** - Build your parlay
5. **Set Stake Amount** - Enter your wager amount
6. **View Current Parlay** - See your parlay summary with potential payout
7. **Clear Parlay** - Start fresh
8. **Exit** - Close the program

### Example Parlay Output

```
==================================================
PARLAY SUMMARY
==================================================
Number of Legs: 2

Selections:
  1. Kansas City Chiefs (h2h) @ -150
  2. Los Angeles Lakers (h2h) @ +110

Combined Odds: +263 (Decimal: 3.63)
Implied Win Probability: 25.71%

Stake: $100.00
Potential Payout: $363.00
Potential Profit: $263.00
==================================================
```

## API Reference

### Odds Conversion Functions

```python
from src.parlay import american_to_decimal, decimal_to_american

# Convert American odds to decimal
decimal_odds = american_to_decimal(-150)  # Returns 1.67

# Convert decimal to American
american_odds = decimal_to_american(2.50)  # Returns 150
```

### Parlay Calculation

```python
from src.parlay import BetSelection, Parlay, calculate_payout

# Create selections
selection1 = BetSelection(
    game_id="game1",
    game_description="Team A @ Team B",
    selection_name="Team A",
    market_type="h2h",
    odds=-150
)

# Build parlay
parlay = Parlay()
parlay.add_selection(selection1)
parlay.set_stake(100.0)

# Calculate payout
payout = calculate_payout(parlay.stake, parlay.selections)
print(f"Potential payout: ${payout['total_payout']:.2f}")
```

## Running Tests

```bash
python -m pytest tests/ -v
```

Or run with unittest:

```bash
python -m unittest discover tests/
```

## Project Structure

```
MyParlai/
├── README.md
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── main.py          # CLI application
│   ├── parlay.py        # Parlay calculations
│   └── sports_data.py   # Sports data API client
└── tests/
    ├── __init__.py
    ├── test_parlay.py
    └── test_sports_data.py
```

## Supported Sports

- 🏈 NFL (American Football)
- 🏀 NBA (Basketball)
- 🏒 NHL (Ice Hockey)
- ⚾ MLB (Baseball)
- ⚽ Soccer (EPL, La Liga, etc.)
- And many more from The Odds API

## License

MIT License
