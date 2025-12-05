# CFB Rankings

A college football ranking system that uses Power 4 conference weighting and strength of victory calculations with head-to-head tiebreakers.

## Ranking Algorithm

The ranking system uses a sophisticated multi-step process to evaluate teams based on their record, strength of schedule, and head-to-head results:

```mermaid
flowchart TD
    A[Start: Raw Game Data] --> B[Filter FBS Teams Only]
    B --> C[Calculate Basic Records<br/>Wins, Losses, Ties]
    
    C --> D[Calculate Strength Metrics]
    D --> D1[Raw Strength of Victory<br/>Sum of defeated opponents' win%]
    D --> D2[Power 4 Weighted SoV<br/>1.5x multiplier for P4 wins]
    
    D1 --> E[Calculate Adjusted Win %]
    D2 --> E
    E --> E1[Formula: 40% Raw Wins + 60% P4 Weighted SoV]
    
    E1 --> F[Sort by Adjusted Win %]
    F --> G[Group Teams by Identical Records]
    
    G --> H{Teams with<br/>Same Record?}
    H -->|Yes| I[Apply Head-to-Head Tiebreakers]
    H -->|No| J[Keep Adjusted Win % Order]
    
    I --> I1[Check for H2H Games<br/>Between Tied Teams]
    I1 --> I2{H2H Violation?<br/>Loser ranked higher<br/>than winner?}
    I2 -->|Yes| I3[Move Winner Above Loser]
    I2 -->|No| I4[Keep Current Order]
    I3 --> I5{More Violations?}
    I4 --> I5
    I5 -->|Yes, <20 iterations| I2
    I5 -->|No or Max Iterations| K[Final Rankings]
    
    J --> K
    K --> L[Display Results with H2H Indicators]
    
    style A fill:#e1f5fe
    style K fill:#c8e6c9
    style L fill:#c8e6c9
    style E1 fill:#fff3e0
    style I2 fill:#ffecb3
```

## Key Features

### Power 4 Conference Weighting
- **SEC, Big Ten, Big 12, ACC** teams receive 1.5x multiplier for strength of victory
- Reflects the generally higher quality of competition in these conferences
- Other conferences (Group of 5, Independents) use standard 1.0x multiplier

### Strength of Victory Calculation
```
Raw SoV = Σ(defeated_opponent_win_percentage)
P4 Weighted SoV = Σ(defeated_opponent_win_percentage × conference_multiplier)
```

### Adjusted Win Percentage Formula
```
Adjusted Win % = (0.4 × Raw Wins) + (0.6 × P4_Weighted_SoV) / Total_Games
```

### Head-to-Head Tiebreakers
- Applied only to teams with **identical win-loss records**
- Checks for head-to-head violations (loser ranked higher than winner)
- Moves winners above losers within the same record group
- Includes cycle detection to prevent infinite loops
- Maximum 20 iterations to handle complex multi-team scenarios

## Usage

```bash
# Basic rankings for current season (2025)
uv run python src/rankings/build.py

# Specify different year
uv run python src/rankings/build.py --year 2024

# Analyze specific team
uv run python src/rankings/build.py --team "Ohio State"

# Compare two teams
uv run python src/rankings/build.py --compare "Oklahoma" "Alabama"

# Generate scatter plot
uv run python src/rankings/build.py --plot

# Download fresh data instead of using local cache
uv run python src/rankings/build.py --update
```

## Example Output

The system shows head-to-head adjustments in real-time:

```
Multiple teams with record (9-2): ['Alabama', 'Oklahoma', 'Utah', 'Virginia', 'Vanderbilt']
  Oklahoma moved above Alabama (H2H win)

Final Rankings:
Rank Team                      Overall Record  FBS Record   Raw Win%  Adj Win%  P4 Wins  SoV     H2H Beat
11   Oklahoma                  10-2            9-2          0.818     0.728     7        7.343   Alabama
12   Alabama                   10-2            9-2          0.818     0.750     8        7.750
```

## Data Sources

- **Live Data**: Sports Reference (sports-reference.com) via web scraping
- **Local Cache**: CSV files stored in `data/schedule_{year}.csv`
- **FBS Team List**: Maintained list of all Division I FBS teams by conference