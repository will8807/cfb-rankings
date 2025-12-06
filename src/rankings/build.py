from pathlib import Path
import random
import argparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt

year = 2025
week = 15

this_dir = Path(__file__).parent.parent.parent
print(this_dir)

def get_schedule(update=False):

    if not update:
        # Use local CSV file by default
        csv_path = Path(this_dir).joinpath("data", f"schedule_{year}.csv")
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            
            # Clean up team names - strip whitespace and remove rankings
            for col in ["Winner", "Loser"]:
                if col in df.columns:
                    # Strip leading/trailing whitespace first
                    df[col] = df[col].str.strip()
                    # Then remove ranking numbers in parentheses
                    df[col] = df[col].str.replace(r"\(\d+\)", "", regex=True)
                    # Strip again after removing rankings
                    df[col] = df[col].str.strip()
            
            print(f"Using local data from: {csv_path}")
            return df
        else:
            print(f"Local file {csv_path} not found. Downloading fresh data...")
            # Fall through to scraping logic

    # Scrape fresh data from web
    print("Scraping fresh data from sports-reference.com...")
    url = f"https://www.sports-reference.com/cfb/years/{year}-schedule.html"

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", id="schedule")
    driver.quit()

    headers = []
    thead = table.find_next("thead")
    for th in thead.find_all("th"):
        headers.append(th.text.strip())

    rows = []
    for tr in table.find_all("tr"):
        cells = [td.text.strip() for td in tr.find_all("td")]
        if cells: # Only add rows that contain data cells (skip header row if already processed)
            rows.append(cells)

    df = pd.DataFrame(rows, columns=headers[1:])  # Exclude the first header "Rk"

    # Remove non-breaking spaces from all string cells
    df = df.map(lambda x: x.replace('\xa0', ' ') if isinstance(x, str) else x)

    # Sanitize team names to get rid of ranking
    for col in ["Winner", "Loser"]:
        if col in df.columns:
            df[col] = df[col].str.replace(r"\(\d+\)", "", regex=True)
            # Strip whitespace again after removing rankings
            df[col] = df[col].str.strip()

    # Save locally
    df.to_csv(Path(this_dir).joinpath("data",f"schedule_{year}.csv"), index=False)
    print(f"Fresh data saved to: {Path(this_dir).joinpath('data', f'schedule_{year}.csv')}")

    return df

def get_fbs_teams():
    """Return list of FBS (Division 1) teams"""
    # Official FBS teams as of 2025 season
    fbs_teams = {
        # ACC
        'Boston College', 'Clemson', 'Duke', 'Florida State', 'Georgia Tech',
        'Louisville', 'Miami (FL)', 'North Carolina', 'North Carolina State',
        'Pittsburgh', 'Syracuse', 'Virginia', 'Virginia Tech', 'Wake Forest',
        
        # Big 12
        'Arizona', 'Arizona State', 'Baylor', 'Brigham Young', 'Cincinnati',
        'Colorado', 'Houston', 'Iowa State', 'Kansas', 'Kansas State',
        'Oklahoma State', 'Texas Christian', 'Texas Tech', 'Utah', 'West Virginia',
        
        # Big Ten
        'Illinois', 'Indiana', 'Iowa', 'Maryland', 'Michigan', 'Michigan State',
        'Minnesota', 'Nebraska', 'Northwestern', 'Ohio State', 'Oregon',
        'Penn State', 'Purdue', 'Rutgers', 'UCLA', 'Southern California',
        'Washington', 'Wisconsin',
        
        # SEC
        'Alabama', 'Arkansas', 'Auburn', 'Florida', 'Georgia', 'Kentucky',
        'Louisiana State', 'Mississippi', 'Mississippi State', 'Missouri',
        'Oklahoma', 'South Carolina', 'Tennessee', 'Texas', 'Texas A&M',
        'Vanderbilt',
        
        # American Athletic Conference
        'East Carolina', 'Memphis', 'Navy', 'South Florida', 'Temple',
        'Tulane', 'Tulsa',
        
        # Conference USA
        'Florida International', 'Louisiana Tech', 'Middle Tennessee State',
        'New Mexico State', 'Texas-El Paso', 'Western Kentucky',
        
        # MAC
        'Akron', 'Ball State', 'Bowling Green', 'Buffalo', 'Central Michigan',
        'Eastern Michigan', 'Kent State', 'Miami (OH)', 'Northern Illinois',
        'Ohio', 'Toledo', 'Western Michigan',
        
        # Mountain West
        'Air Force', 'Boise State', 'Colorado State', 'Fresno State',
        'Nevada', 'Nevada-Las Vegas', 'New Mexico', 'San Diego State',
        'San Jose State', 'Utah State', 'Wyoming',
        
        # Pac-12
        'California', 'Oregon State', 'Stanford', 'Washington State',
        
        # Sun Belt
        'Appalachian State', 'Arkansas State', 'Coastal Carolina',
        'Georgia Southern', 'Georgia State', 'James Madison', 'Louisiana',
        'Louisiana-Monroe', 'Marshall', 'Old Dominion', 'South Alabama',
        'Southern Mississippi', 'Texas State', 'Troy',
        
        # Independents
        'Army', 'Connecticut', 'Massachusetts', 'Notre Dame',
        
        # Additional FBS teams
        'Alabama-Birmingham', 'Central Florida', 'Charlotte', 'Florida Atlantic',
        'Liberty', 'Rice', 'Texas-San Antonio'
    }
    
    return fbs_teams

def get_teams(schedule_df):
    winners = schedule_df["Winner"].unique().tolist()
    losers = schedule_df["Loser"].unique().tolist()
    all_teams = list(set(winners) | set(losers))
    
    # Filter to only include FBS teams
    fbs_team_set = get_fbs_teams()
    fbs_teams = [team for team in all_teams if team in fbs_team_set]
    fbs_teams.sort()
    
    print(f"Total teams found: {len(all_teams)}")
    print(f"FBS teams after filtering: {len(fbs_teams)}")
    print(f"Non-FBS teams filtered out: {len(all_teams) - len(fbs_teams)}")
    
    # Show teams that weren't recognized as FBS
    non_fbs = [team for team in all_teams if team not in fbs_team_set]
    if non_fbs:
        print(f"Non-FBS teams found: {sorted(non_fbs)[:10]}...")  # Show first 10
    
    return fbs_teams

def filter_schedule_fbs_only(schedule_df, fbs_teams):
    """Filter schedule to only include games between FBS teams and within week limit"""
    fbs_set = set(fbs_teams)
    fbs_schedule = schedule_df[
        (schedule_df["Winner"].isin(fbs_set)) & 
        (schedule_df["Loser"].isin(fbs_set)) &
        (schedule_df["Wk"] <= week)  # Filter by week cutoff
    ].copy()
    
    print(f"Original games: {len(schedule_df)}")
    print(f"FBS-only games through week {week}: {len(fbs_schedule)}")
    
    return fbs_schedule

def calculate_strength_of_schedule(schedule_df, teams):
    """Calculate strength of schedule based on opponents' win percentage"""
    
    # Calculate wins and losses for each team
    team_records = {team: {'wins': 0, 'losses': 0, 'opponents': []} for team in teams}
    
    # Count wins/losses and track opponents
    for _, game in schedule_df.iterrows():
        winner = game["Winner"]
        loser = game["Loser"]
        
        if winner in team_records and loser in team_records:
            team_records[winner]['wins'] += 1
            team_records[loser]['losses'] += 1
            team_records[winner]['opponents'].append(loser)
            team_records[loser]['opponents'].append(winner)
    
    # Calculate win percentages
    win_percentages = {}
    for team, record in team_records.items():
        total_games = record['wins'] + record['losses']
        win_percentages[team] = record['wins'] / total_games if total_games > 0 else 0
    
    # Calculate strength of schedule (average opponent win percentage)
    sos = {}
    for team, record in team_records.items():
        if record['opponents']:
            opponent_win_pcts = [win_percentages[opp] for opp in record['opponents']]
            sos[team] = sum(opponent_win_pcts) / len(opponent_win_pcts)
        else:
            sos[team] = 0
    
    return sos, win_percentages, team_records

def get_rankings(schedule_df, teams, create_plot=False):
    """Calculate rankings using adjusted win percentage"""
    # Calculate win-loss records for all FBS teams
    team_records = {}
    team_overall_records = {}
    
    # Initialize records
    for team in teams:
        team_records[team] = {'wins': 0, 'losses': 0, 'ties': 0, 'opponents': []}
        team_overall_records[team] = {'wins': 0, 'losses': 0, 'ties': 0}
    
    # Get overall records from all games (before FBS filtering)
    overall_schedule = get_schedule()
    # Filter by week cutoff
    overall_schedule = overall_schedule[overall_schedule["Wk"] <= week]
    
    for _, game in overall_schedule.iterrows():
        winner = game["Winner"]
        loser = game["Loser"]
        
        if winner in team_overall_records:
            team_overall_records[winner]['wins'] += 1
        if loser in team_overall_records:
            team_overall_records[loser]['losses'] += 1
    
    # Count wins and losses from FBS games only, track defeated and lost-to opponents
    for _, game in schedule_df.iterrows():
        winner = game["Winner"]
        loser = game["Loser"]
        
        if winner in team_records and loser in team_records:
            team_records[winner]['wins'] += 1
            team_records[loser]['losses'] += 1
            team_records[winner]['opponents'].append(('defeated', loser))
            team_records[loser]['opponents'].append(('lost_to', winner))
    
    # Calculate opponent win rates first
    opponent_win_rates = {}
    for team, record in team_records.items():
        total_games = record['wins'] + record['losses'] + record['ties']
        opponent_win_rates[team] = record['wins'] / total_games if total_games > 0 else 0.000
    
    # Calculate adjusted win percentage using Strength of Victory
    team_stats = []
    for team, record in team_records.items():
        total_games = record['wins'] + record['losses'] + record['ties']
        raw_win_pct = record['wins'] / total_games if total_games > 0 else 0.000
        
        # Calculate Strength of Victory with Power 4 conference weighting
        strength_of_victory = 0.0
        strength_of_schedule = 0.0
        defeated_opponents = []
        lost_to_opponents = []
        quality_wins = 0  # Track wins against quality teams
        power4_wins = 0   # Track wins against Power 4 teams
        
        # Define Power 4 conferences (approximate based on major conferences)
        power4_teams = {
            # SEC
            'Alabama', 'Arkansas', 'Auburn', 'Florida', 'Georgia', 'Kentucky', 'Louisiana State', 
            'Mississippi', 'Mississippi State', 'Missouri', 'South Carolina', 'Tennessee', 
            'Texas', 'Texas A&M', 'Vanderbilt', 'Oklahoma',
            
            # Big Ten  
            'Illinois', 'Indiana', 'Iowa', 'Maryland', 'Michigan', 'Michigan State', 'Minnesota',
            'Nebraska', 'Northwestern', 'Ohio State', 'Oregon', 'Penn State', 'Purdue', 
            'Rutgers', 'Southern California', 'UCLA', 'Washington', 'Wisconsin',
            
            # Big 12
            'Arizona', 'Arizona State', 'Baylor', 'Brigham Young', 'Cincinnati', 'Colorado', 
            'Houston', 'Iowa State', 'Kansas', 'Kansas State', 'Oklahoma State', 'Texas Christian', 
            'Texas Tech', 'Utah', 'West Virginia',
            
            # ACC
            'Boston College', 'California', 'Clemson', 'Duke', 'Florida State', 'Georgia Tech',
            'Louisville', 'Miami (FL)', 'North Carolina', 'North Carolina State', 'Notre Dame',
            'Pittsburgh', 'Stanford', 'Syracuse', 'Virginia', 'Virginia Tech', 'Wake Forest'
        }
        
        # Simplified Strength of Victory calculation
        for result_type, opponent in record['opponents']:
            if result_type == 'defeated':
                defeated_opponents.append(opponent)
                opp_win_rate = opponent_win_rates[opponent]
                
                # Calculate weighted opponent value
                if opponent in power4_teams:
                    power4_wins += 1
                    # Power 4 multiplier: 1.5x opponent win rate, minimum 0.75
                    opponent_value = max(0.75, opp_win_rate * 1.5)
                else:
                    # Non-Power 4: just use opponent win rate
                    opponent_value = opp_win_rate
                
                strength_of_victory += opponent_value
                if opp_win_rate > 0.500:  # Still track quality wins
                    quality_wins += 1
                    
            elif result_type == 'lost_to':
                lost_to_opponents.append(opponent)
                strength_of_schedule += opponent_win_rates[opponent]
        
        # Average opponent win rates
        avg_defeated_win_rate = strength_of_victory / quality_wins if quality_wins > 0 else 0.0
        avg_lost_to_win_rate = strength_of_schedule / len(lost_to_opponents) if lost_to_opponents else 0.0
        avg_opp_win_rate = (strength_of_victory + strength_of_schedule) / len(record['opponents']) if record['opponents'] else 0.0
        
        # Quality-based Adjusted Win % (no penalties)
        if total_games > 0:
            # Base formula: 40% raw wins, 60% strength of victory
            adjusted_wins = (0.4 * record['wins']) + (0.6 * strength_of_victory)
            
            # No penalties applied
            
            adjusted_win_pct = adjusted_wins / total_games
        else:
            adjusted_win_pct = 0.000
        
        overall_record = team_overall_records[team]
        
        team_stats.append({
            'team': team,
            'wins': record['wins'],
            'losses': record['losses'],
            'ties': record['ties'],
            'total_games': total_games,
            'raw_win_pct': raw_win_pct,
            'adjusted_win_pct': adjusted_win_pct,
            'avg_opp_win_rate': avg_opp_win_rate,
            'avg_defeated_win_rate': avg_defeated_win_rate,
            'avg_lost_to_win_rate': avg_lost_to_win_rate,
            'strength_of_victory': strength_of_victory,
            'quality_wins': quality_wins,
            'power4_wins': power4_wins,
            'overall_wins': overall_record['wins'],
            'overall_losses': overall_record['losses'],
            'overall_ties': overall_record['ties'],
            'defeated_opponents': defeated_opponents,
            'lost_to_opponents': lost_to_opponents,
            'h2h_tiebreaker': False,  # Track if head-to-head tiebreaker was applied
            'h2h_beaten_team': None   # Track which team was beaten in head-to-head
        })
    
    # Apply head-to-head tiebreaker only for teams with very similar adjusted win percentages
    def head_to_head_tiebreaker(teams):
        """Apply head-to-head tiebreaking for teams with similar adjusted win percentages."""
        # Make one pass through the sorted teams looking for head-to-head violations
        result = teams.copy()
        changes_made = True
        iteration_count = 0
        max_iterations = 3
        
        while changes_made and iteration_count < max_iterations:
            changes_made = False
            iteration_count += 1
            
            for i in range(len(result)):
                for j in range(i + 1, len(result)):
                    team_higher = result[i]  # Currently ranked higher
                    team_lower = result[j]   # Currently ranked lower
                    
                    # Check if the lower-ranked team beat the higher-ranked team
                    if team_higher['team'] in team_lower['defeated_opponents']:
                        # Also check if their adj win % is close enough to justify H2H tiebreaker
                        adj_win_diff = abs(team_higher['adjusted_win_pct'] - team_lower['adjusted_win_pct'])
                        
                        # Only apply H2H if teams are close in adj win % (within 0.025)
                        if adj_win_diff <= 0.025:
                            # H2H violation: lower team beat higher team, so move lower team above
                            result.pop(j)  # Remove from current position
                            result.insert(i, team_lower)  # Insert at higher position
                            team_lower['h2h_tiebreaker'] = True
                            team_lower['h2h_beaten_team'] = team_higher['team']
                            print(f"  {team_lower['team']} moved above {team_higher['team']} (H2H win)")
                            changes_made = True
                            break
                if changes_made:
                    break
        
        if iteration_count >= max_iterations:
            print(f"  Stopped H2H adjustments after {max_iterations} iterations")
        
        return result
    
    # Sort by adjusted win percentage first (primary ranking criteria)
    team_stats.sort(key=lambda x: x['adjusted_win_pct'], reverse=True)
    
    # Apply head-to-head tiebreaker only for teams with very similar adjusted win percentages
    team_stats = head_to_head_tiebreaker(team_stats)
    
    print("Final Rankings (Power 4 Conference Weighted Win Percentage):")
    print("=" * 105)
    print(f"{'Rank':<4} {'Team':<25} {'Overall Record':<15} {'FBS Record':<12} {'Raw Win%':<9} {'Adj Win%':<9} {'P4 Wins':<8} {'SoV':<7} {'H2H Beat':<12}")
    print("=" * 105)
    for rank, stats in enumerate(team_stats[:25], start=1):
        team = stats['team']
        wins = stats['wins']
        losses = stats['losses']
        ties = stats['ties']
        raw_win_pct = stats['raw_win_pct']
        adjusted_win_pct = stats['adjusted_win_pct']
        power4_wins = stats['power4_wins']
        strength_of_victory = stats['strength_of_victory']
        
        overall_wins = stats['overall_wins']
        overall_losses = stats['overall_losses']
        overall_ties = stats['overall_ties']
        
        # Format record strings
        if ties > 0:
            fbs_record_str = f"{wins}-{losses}-{ties}"
        else:
            fbs_record_str = f"{wins}-{losses}"
            
        if overall_ties > 0:
            overall_record_str = f"{overall_wins}-{overall_losses}-{overall_ties}"
        else:
            overall_record_str = f"{overall_wins}-{overall_losses}"
        
        # Head-to-head indicator - show beaten team name
        h2h_indicator = stats.get('h2h_beaten_team', '') if stats.get('h2h_tiebreaker', False) else ""
        
        print(f"{rank:<4} {team:<25} {overall_record_str:<15} {fbs_record_str:<12} {raw_win_pct:.3f}     {adjusted_win_pct:.3f}     {power4_wins:<8} {strength_of_victory:.3f} {h2h_indicator:<12}")
    
    print("\nLegend: H2H Beat = Team that was beaten head-to-head to earn higher ranking")
    
    # Create scatter plot for top 25 if requested (using adjusted win % for y-axis)
    if create_plot:
        create_adjusted_scatter_plot(team_stats[:25])
    
    # Return as dictionary for consistency
    return {stats['team']: rank for rank, stats in enumerate(team_stats, start=1)}


def get_team_schedule(schedule_df, team_name, rankings_dict=None):
    """Extract a team's schedule with opponent records and rankings for analysis"""
    
    # Find all games involving the specified team
    team_games = schedule_df[
        (schedule_df["Winner"] == team_name) | (schedule_df["Loser"] == team_name)
    ].copy()
    
    if team_games.empty:
        print(f"No games found for team: {team_name}")
        print(f"Available teams: {sorted(set(schedule_df['Winner'].tolist() + schedule_df['Loser'].tolist()))[:10]}...")
        return None
    
    # Calculate opponent records
    all_teams = set(schedule_df["Winner"].tolist() + schedule_df["Loser"].tolist())
    opponent_records = {}
    
    for team in all_teams:
        wins = len(schedule_df[schedule_df["Winner"] == team])
        losses = len(schedule_df[schedule_df["Loser"] == team])
        opponent_records[team] = {'wins': wins, 'losses': losses, 'win_pct': wins / (wins + losses) if (wins + losses) > 0 else 0}

    # Process each game
    schedule_analysis = []
    team_wins = 0
    team_losses = 0
    
    for _, game in team_games.iterrows():
        is_winner = game["Winner"] == team_name
        opponent = game["Loser"] if is_winner else game["Winner"]
        result = "W" if is_winner else "L"
        
        if is_winner:
            team_wins += 1
        else:
            team_losses += 1


def get_team_schedule(schedule_df, team_name, rankings_dict=None):
    """Extract a team's schedule with opponent records and rankings for analysis"""
    
    # Find all games involving the specified team (FBS only)
    team_games = schedule_df[
        (schedule_df["Winner"] == team_name) | (schedule_df["Loser"] == team_name)
    ].copy()
    
    if team_games.empty:
        print(f"No games found for team: {team_name}")
        print(f"Available teams: {sorted(set(schedule_df['Winner'].tolist() + schedule_df['Loser'].tolist()))[:10]}...")
        return None
    
    # Get overall schedule to calculate overall record (including FCS games)
    overall_schedule = get_schedule()
    overall_schedule = overall_schedule[overall_schedule["Wk"] <= week]
    overall_games = overall_schedule[
        (overall_schedule["Winner"] == team_name) | (overall_schedule["Loser"] == team_name)
    ].copy()
    
    # Calculate overall record (all games)
    overall_wins = len(overall_games[overall_games["Winner"] == team_name])
    overall_losses = len(overall_games[overall_games["Loser"] == team_name])
    
    # Calculate opponent records
    all_teams = set(schedule_df["Winner"].tolist() + schedule_df["Loser"].tolist())
    opponent_records = {}
    
    for team in all_teams:
        wins = len(schedule_df[schedule_df["Winner"] == team])
        losses = len(schedule_df[schedule_df["Loser"] == team])
        opponent_records[team] = {'wins': wins, 'losses': losses, 'win_pct': wins / (wins + losses) if (wins + losses) > 0 else 0}
    
    # Process each game
    schedule_analysis = []
    team_wins = 0  # FBS wins
    team_losses = 0  # FBS losses
    
    for _, game in team_games.iterrows():
        is_winner = game["Winner"] == team_name
        opponent = game["Loser"] if is_winner else game["Winner"]
        result = "W" if is_winner else "L"
        
        if is_winner:
            team_wins += 1
        else:
            team_losses += 1
        
        # Get opponent record and ranking
        opp_record = opponent_records[opponent]
        opp_rank = rankings_dict.get(opponent, "NR") if rankings_dict else "N/A"
        
        schedule_analysis.append({
            'week': game.get("Wk", "?"),
            'opponent': opponent,
            'result': result,
            'opponent_record': f"{opp_record['wins']}-{opp_record['losses']}",
            'opponent_win_pct': opp_record['win_pct'],
            'opponent_rank': opp_rank
        })
    
    # Sort by week
    schedule_analysis.sort(key=lambda x: x['week'] if isinstance(x['week'], (int, float)) else 999)
    
    # Define Power 4 teams for calculation
    power4_teams = {
        # SEC
        'Alabama', 'Arkansas', 'Auburn', 'Florida', 'Georgia', 'Kentucky', 'Louisiana State', 
        'Mississippi', 'Mississippi State', 'Missouri', 'South Carolina', 'Tennessee', 
        'Texas', 'Texas A&M', 'Vanderbilt', 'Oklahoma',
        
        # Big Ten  
        'Illinois', 'Indiana', 'Iowa', 'Maryland', 'Michigan', 'Michigan State', 'Minnesota',
        'Nebraska', 'Northwestern', 'Ohio State', 'Oregon', 'Penn State', 'Purdue', 
        'Rutgers', 'Southern California', 'UCLA', 'Washington', 'Wisconsin',
        
        # Big 12
        'Arizona', 'Arizona State', 'Baylor', 'Brigham Young', 'Cincinnati', 'Colorado', 
        'Houston', 'Iowa State', 'Kansas', 'Kansas State', 'Oklahoma State', 'Texas Christian', 
        'Texas Tech', 'Utah', 'West Virginia',
        
        # ACC
        'Boston College', 'California', 'Clemson', 'Duke', 'Florida State', 'Georgia Tech',
        'Louisville', 'Miami (FL)', 'North Carolina', 'North Carolina State', 'Notre Dame',
        'Pittsburgh', 'Stanford', 'Syracuse', 'Virginia', 'Virginia Tech', 'Wake Forest'
    }
    
    # Calculate adjusted win percentage for display
    strength_of_victory = 0.0
    for game in schedule_analysis:
        if game['result'] == 'W':
            opponent = game['opponent']
            opp_win_pct = game['opponent_win_pct']
            
            if opponent in power4_teams:
                # Power 4 multiplier: 1.5x opponent win rate, minimum 0.75
                opponent_value = max(0.75, opp_win_pct * 1.5)
            else:
                # Non-Power 4: just use opponent win rate
                opponent_value = opp_win_pct
                
            strength_of_victory += opponent_value
    
    # Calculate adjusted win percentage
    raw_win_pct = team_wins / (team_wins + team_losses) if (team_wins + team_losses) > 0 else 0
    total_games = team_wins + team_losses
    
    if total_games > 0:
        # Base formula: 40% raw wins, 60% strength of victory
        adjusted_wins = (0.4 * team_wins) + (0.6 * strength_of_victory)
        adjusted_win_pct = adjusted_wins / total_games
    else:
        adjusted_win_pct = 0
    
    # Print analysis
    print(f"\n{team_name} Schedule Analysis")
    print("=" * 80)
    print(f"Overall Record: {overall_wins}-{overall_losses} ({overall_wins/(overall_wins+overall_losses)*100:.1f}%)")
    print(f"FBS Record: {team_wins}-{team_losses} ({team_wins/(team_wins+team_losses)*100:.1f}%) | Raw Win%: {raw_win_pct:.3f} | Adj Win%: {adjusted_win_pct:.3f}")
    print("=" * 95)
    print(f"{'Week':<4} {'Opponent':<25} {'Result':<6} {'Opp Record':<11} {'Opp Win%':<8} {'P4':<3} {'Value':<6} {'Opp Rank':<8}")
    print("-" * 95)
    
    # Define Power 4 teams for table display
    power4_teams = {
        # SEC
        'Alabama', 'Arkansas', 'Auburn', 'Florida', 'Georgia', 'Kentucky', 'Louisiana State', 
        'Mississippi', 'Mississippi State', 'Missouri', 'South Carolina', 'Tennessee', 
        'Texas', 'Texas A&M', 'Vanderbilt', 'Oklahoma',
        
        # Big Ten  
        'Illinois', 'Indiana', 'Iowa', 'Maryland', 'Michigan', 'Michigan State', 'Minnesota',
        'Nebraska', 'Northwestern', 'Ohio State', 'Oregon', 'Penn State', 'Purdue', 
        'Rutgers', 'Southern California', 'UCLA', 'Washington', 'Wisconsin',
        
        # Big 12
        'Arizona', 'Arizona State', 'Baylor', 'Brigham Young', 'Cincinnati', 'Colorado', 
        'Houston', 'Iowa State', 'Kansas', 'Kansas State', 'Oklahoma State', 'Texas Christian', 
        'Texas Tech', 'Utah', 'West Virginia',
        
        # ACC
        'Boston College', 'California', 'Clemson', 'Duke', 'Florida State', 'Georgia Tech',
        'Louisville', 'Miami (FL)', 'North Carolina', 'North Carolina State', 'Notre Dame',
        'Pittsburgh', 'Stanford', 'Syracuse', 'Virginia', 'Virginia Tech', 'Wake Forest'
    }
    
    for game in schedule_analysis:
        week_str = str(game['week']) if game['week'] != "?" else "?"
        opponent = game['opponent']
        result = game['result']
        opp_win_pct = game['opponent_win_pct']
        
        # Determine if Power 4 team
        is_power4 = "Yes" if opponent in power4_teams else "No"
        
        # Calculate victory value (only for wins)
        if result == 'W':
            if opponent in power4_teams:
                victory_value = max(0.75, opp_win_pct * 1.5)
            else:
                victory_value = opp_win_pct
            value_str = f"{victory_value:.3f}"
        else:
            value_str = "-"
        
        print(f"{week_str:<4} {opponent:<25} {result:<6} {game['opponent_record']:<11} "
              f"{opp_win_pct:.3f}    {is_power4:<3} {value_str:<6} {game['opponent_rank']}")
    
    # Calculate strength of schedule metrics
    total_opp_wins = sum(opponent_records[game['opponent']]['wins'] for game in schedule_analysis)
    total_opp_losses = sum(opponent_records[game['opponent']]['losses'] for game in schedule_analysis)
    avg_opp_win_pct = sum(game['opponent_win_pct'] for game in schedule_analysis) / len(schedule_analysis)
    
    print("-" * 95)
    print(f"Strength of Schedule Metrics (FBS only):")
    print(f"  Total Opponent FBS Wins: {total_opp_wins}")
    print(f"  Total Opponent FBS Losses: {total_opp_losses}")
    print(f"  Average Opponent FBS Win%: {avg_opp_win_pct:.3f}")
    print(f"  Games vs Ranked Teams: {sum(1 for game in schedule_analysis if isinstance(game['opponent_rank'], int))}")
    
    return schedule_analysis

def create_top25_scatter_plot(team_stats):
    """Create a scatter plot of wins vs strength of schedule for top 25 teams"""
    
    # Extract data for plotting
    wins = [stats['wins'] for stats in team_stats]
    sos = [stats['sos'] for stats in team_stats]
    team_names = [stats['team'] for stats in team_stats]
    
    # Create the scatter plot
    plt.figure(figsize=(12, 8))
    scatter = plt.scatter(wins, sos, c=range(len(team_stats)), cmap='viridis', s=100, alpha=0.7)
    
    # Customize the plot
    plt.xlabel('FBS Wins', fontsize=12)
    plt.ylabel('Strength of Schedule (Opponent Win %)', fontsize=12)
    plt.title('Top 25 Teams: FBS Wins vs Strength of Schedule', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    
    # Add team labels for top teams (avoid overcrowding)
    for i, (x, y, name) in enumerate(zip(wins, sos, team_names)):
        if i < 10:  # Label top 10 teams
            plt.annotate(f'{i+1}. {name}', (x, y), xytext=(5, 5), 
                        textcoords='offset points', fontsize=8, alpha=0.8)
    
    # Add colorbar to show rankings
    cbar = plt.colorbar(scatter)
    cbar.set_label('Ranking (1-25)', fontsize=10)
    
    # Set axis limits with some padding
    plt.xlim(min(wins) - 0.5, max(wins) + 0.5)
    plt.ylim(min(sos) - 0.02, max(sos) + 0.02)
    
    # Add some context annotations
    plt.figtext(0.02, 0.02, 'Top-right: High wins + tough schedule | Bottom-right: High wins + weak schedule', 
                fontsize=9, style='italic', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig('top25_wins_vs_sos.png', dpi=300, bbox_inches='tight')
    print(f"\nScatter plot saved as 'top25_wins_vs_sos.png'")
    plt.show()

def create_adjusted_scatter_plot(team_stats):
    """Create a scatter plot of wins vs adjusted win percentage for top 25 teams"""
    
    # Extract data for plotting
    wins = [stats['wins'] for stats in team_stats]
    adjusted_win_pct = [stats['adjusted_win_pct'] for stats in team_stats]
    raw_win_pct = [stats['raw_win_pct'] for stats in team_stats]
    team_names = [stats['team'] for stats in team_stats]
    
    # Create the scatter plot
    plt.figure(figsize=(12, 8))
    scatter = plt.scatter(wins, adjusted_win_pct, c=range(len(team_stats)), cmap='viridis', s=100, alpha=0.7)
    
    # Customize the plot
    plt.xlabel('FBS Wins', fontsize=12)
    plt.ylabel('Adjusted Win Percentage', fontsize=12)
    plt.title('Top 25 Teams: FBS Wins vs Adjusted Win Percentage', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    
    # Add team labels for top teams (avoid overcrowding)
    for i, (x, y, name) in enumerate(zip(wins, adjusted_win_pct, team_names)):
        if i < 10:  # Label top 10 teams
            plt.annotate(f'{i+1}. {name}', (x, y), xytext=(5, 5), 
                        textcoords='offset points', fontsize=8, alpha=0.8)
    
    # Add colorbar to show rankings
    cbar = plt.colorbar(scatter)
    cbar.set_label('Ranking (1-25)', fontsize=10)
    
    # Set axis limits with some padding
    plt.xlim(min(wins) - 0.5, max(wins) + 0.5)
    plt.ylim(min(adjusted_win_pct) - 0.02, max(adjusted_win_pct) + 0.02)
    
    # Add some context annotations
    plt.figtext(0.02, 0.02, 'Adjusted Win% = (Wins + Losses * Avg_Opponent_Win_Rate) / Total_Games', 
                fontsize=9, style='italic', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig('top25_adjusted_win_pct.png', dpi=300, bbox_inches='tight')
    print(f"\nAdjusted win% scatter plot saved as 'top25_adjusted_win_pct.png'")
    plt.show()

def compare_teams(schedule_df, team1_name, team2_name, rankings_dict=None):
    """Compare two teams' records, strength of schedule, and opponents"""
    
    teams = [team1_name, team2_name]
    team_data = {}
    
    # Get all available teams for validation
    all_teams = set(schedule_df["Winner"].tolist() + schedule_df["Loser"].tolist())
    
    # Validate team names
    for team in teams:
        if team not in all_teams:
            print(f"Team '{team}' not found!")
            print(f"Available teams: {sorted(list(all_teams))[:10]}...")
            return None
    
    # Calculate team records and opponents
    for team in teams:
        team_games = schedule_df[
            (schedule_df["Winner"] == team) | (schedule_df["Loser"] == team)
        ].copy()
        
        wins = 0
        losses = 0
        defeated_opponents = []
        lost_to_opponents = []
        
        for _, game in team_games.iterrows():
            if game["Winner"] == team:
                wins += 1
                defeated_opponents.append(game["Loser"])
            else:
                losses += 1
                lost_to_opponents.append(game["Winner"])
        
        # Calculate opponent records and SOS
        all_opponents = defeated_opponents + lost_to_opponents
        opponent_records = {}
        total_opp_wins = 0
        total_opp_losses = 0
        
        for opponent in all_opponents:
            opp_wins = len(schedule_df[schedule_df["Winner"] == opponent])
            opp_losses = len(schedule_df[schedule_df["Loser"] == opponent])
            opponent_records[opponent] = {
                'wins': opp_wins, 
                'losses': opp_losses,
                'win_pct': opp_wins / (opp_wins + opp_losses) if (opp_wins + opp_losses) > 0 else 0
            }
            total_opp_wins += opp_wins
            total_opp_losses += opp_losses
        
        # Calculate SOS (average opponent win percentage)
        avg_opp_win_pct = sum(opp['win_pct'] for opp in opponent_records.values()) / len(opponent_records) if opponent_records else 0
        
        # Calculate SOS for defeated opponents only
        defeated_opp_win_pct = 0
        if defeated_opponents:
            defeated_opp_win_pct = sum(opponent_records[opp]['win_pct'] for opp in defeated_opponents) / len(defeated_opponents)
        
        # Calculate adjusted win percentage
        # Define Power 4 teams
        power4_teams = {
            # SEC
            'Alabama', 'Arkansas', 'Auburn', 'Florida', 'Georgia', 'Kentucky', 'Louisiana State', 
            'Mississippi', 'Mississippi State', 'Missouri', 'South Carolina', 'Tennessee', 
            'Texas', 'Texas A&M', 'Vanderbilt', 'Oklahoma',
            
            # Big Ten  
            'Illinois', 'Indiana', 'Iowa', 'Maryland', 'Michigan', 'Michigan State', 'Minnesota',
            'Nebraska', 'Northwestern', 'Ohio State', 'Oregon', 'Penn State', 'Purdue', 
            'Rutgers', 'Southern California', 'UCLA', 'Washington', 'Wisconsin',
            
            # Big 12
            'Arizona', 'Arizona State', 'Baylor', 'Brigham Young', 'Cincinnati', 'Colorado', 
            'Houston', 'Iowa State', 'Kansas', 'Kansas State', 'Oklahoma State', 'Texas Christian', 
            'Texas Tech', 'Utah', 'West Virginia',
            
            # ACC
            'Boston College', 'California', 'Clemson', 'Duke', 'Florida State', 'Georgia Tech',
            'Louisville', 'Miami (FL)', 'North Carolina', 'North Carolina State', 'Notre Dame',
            'Pittsburgh', 'Stanford', 'Syracuse', 'Virginia', 'Virginia Tech', 'Wake Forest'
        }
        
        # Calculate strength of victory
        strength_of_victory = 0.0
        for opponent in defeated_opponents:
            opp_win_pct = opponent_records[opponent]['win_pct']
            
            if opponent in power4_teams:
                # Power 4 multiplier: 1.5x opponent win rate, minimum 0.75
                opponent_value = max(0.75, opp_win_pct * 1.5)
            else:
                # Non-Power 4: just use opponent win rate
                opponent_value = opp_win_pct
                
            strength_of_victory += opponent_value
        
        # Calculate adjusted win percentage
        total_games = wins + losses
        if total_games > 0:
            # Base formula: 40% raw wins, 60% strength of victory
            adjusted_wins = (0.4 * wins) + (0.6 * strength_of_victory)
            adjusted_win_pct = adjusted_wins / total_games
        else:
            adjusted_win_pct = 0
        
        team_data[team] = {
            'wins': wins,
            'losses': losses,
            'win_pct': wins / (wins + losses) if (wins + losses) > 0 else 0,
            'adjusted_win_pct': adjusted_win_pct,
            'strength_of_victory': strength_of_victory,
            'defeated_opponents': defeated_opponents,
            'lost_to_opponents': lost_to_opponents,
            'all_opponents': all_opponents,
            'opponent_records': opponent_records,
            'avg_opp_win_pct': avg_opp_win_pct,
            'defeated_opp_win_pct': defeated_opp_win_pct,
            'total_opp_wins': total_opp_wins,
            'total_opp_losses': total_opp_losses,
            'rank': rankings_dict.get(team, "NR") if rankings_dict else "N/A"
        }
    
    # Display comparison
    print(f"\n{'='*80}")
    print(f"TEAM COMPARISON: {team1_name} vs {team2_name}")
    print(f"{'='*80}")
    
    # Head-to-head record
    h2h_games = schedule_df[
        ((schedule_df["Winner"] == team1_name) & (schedule_df["Loser"] == team2_name)) |
        ((schedule_df["Winner"] == team2_name) & (schedule_df["Loser"] == team1_name))
    ]
    
    if not h2h_games.empty:
        print(f"\nHEAD-TO-HEAD:")
        for _, game in h2h_games.iterrows():
            winner = game["Winner"]
            loser = game["Loser"]
            week = game.get("Wk", "?")
            print(f"  Week {week}: {winner} defeated {loser}")
    else:
        print(f"\nHEAD-TO-HEAD: No games between these teams")
    
    # Basic stats comparison
    print(f"\nBASIC STATS:")
    print(f"{'Metric':<25} {team1_name:<15} {team2_name:<15}")
    print("-" * 55)
    print(f"{'FBS Record':<25} {team_data[team1_name]['wins']}-{team_data[team1_name]['losses']:<14} {team_data[team2_name]['wins']}-{team_data[team2_name]['losses']}")
    print(f"{'Win Percentage':<25} {team_data[team1_name]['win_pct']:.3f}           {team_data[team2_name]['win_pct']:.3f}")
    print(f"{'Adjusted Win%':<25} {team_data[team1_name]['adjusted_win_pct']:.3f}           {team_data[team2_name]['adjusted_win_pct']:.3f}")
    print(f"{'Strength of Victory':<25} {team_data[team1_name]['strength_of_victory']:.3f}           {team_data[team2_name]['strength_of_victory']:.3f}")
    print(f"{'Ranking':<25} {team_data[team1_name]['rank']:<15} {team_data[team2_name]['rank']}")
    
    # Strength of Schedule comparison
    print(f"\nSTRENGTH OF SCHEDULE:")
    print(f"{'Metric':<25} {team1_name:<15} {team2_name:<15}")
    print("-" * 55)
    print(f"{'All Opponents Win%':<25} {team_data[team1_name]['avg_opp_win_pct']:.3f}           {team_data[team2_name]['avg_opp_win_pct']:.3f}")
    print(f"{'Defeated Opponents Win%':<25} {team_data[team1_name]['defeated_opp_win_pct']:.3f}           {team_data[team2_name]['defeated_opp_win_pct']:.3f}")
    print(f"{'Total Opponent Wins':<25} {team_data[team1_name]['total_opp_wins']:<15} {team_data[team2_name]['total_opp_wins']}")
    
    # Common opponents
    team1_opponents = set(team_data[team1_name]['all_opponents'])
    team2_opponents = set(team_data[team2_name]['all_opponents'])
    common_opponents = team1_opponents.intersection(team2_opponents)
    
    if common_opponents:
        print(f"\nCOMMON OPPONENTS ({len(common_opponents)} teams):")
        print(f"{'Opponent':<25} {team1_name + ' Result':<15} {team2_name + ' Result':<15} {'Opp Record':<12}")
        print("-" * 67)
        
        for opponent in sorted(common_opponents):
            # Get results vs this opponent
            team1_result = "W" if opponent in team_data[team1_name]['defeated_opponents'] else "L"
            team2_result = "W" if opponent in team_data[team2_name]['defeated_opponents'] else "L"
            opp_record = team_data[team1_name]['opponent_records'][opponent]
            
            print(f"{opponent:<25} {team1_result:<15} {team2_result:<15} {opp_record['wins']}-{opp_record['losses']}")
    else:
        print(f"\nCOMMON OPPONENTS: None")
    
    # Best wins comparison
    print(f"\nBEST WINS (Top 3 by opponent win %):")
    for i, team in enumerate(teams):
        defeated_opps = team_data[team]['defeated_opponents']
        if defeated_opps:
            best_wins = sorted(defeated_opps, 
                             key=lambda x: team_data[team]['opponent_records'][x]['win_pct'], 
                             reverse=True)[:3]
            print(f"\n{team}:")
            for j, opp in enumerate(best_wins, 1):
                opp_data = team_data[team]['opponent_records'][opp]
                opp_rank = rankings_dict.get(opp, "NR") if rankings_dict else "N/A"
                print(f"  {j}. {opp} ({opp_data['wins']}-{opp_data['losses']}, {opp_data['win_pct']:.3f}, Rank: {opp_rank})")
        else:
            print(f"\n{team}: No wins")
    
    print(f"\n{'='*80}")
    return team_data

def main():
    parser = argparse.ArgumentParser(description='College Football Rankings Calculator')
    parser.add_argument('--update', action='store_true', 
                        help='Download fresh data from sports-reference.com (default: use local CSV)')
    parser.add_argument('--year', type=int, default=2025,
                        help='Season year to analyze (default: 2025)')
    parser.add_argument('--team', type=str,
                        help='Analyze schedule for specific team (e.g., "Ohio State")')
    parser.add_argument('--compare', type=str, nargs=2, metavar=('TEAM1', 'TEAM2'),
                        help='Compare two teams (e.g., --compare "Ohio State" "Michigan")')
    parser.add_argument('--plot', action='store_true',
                        help='Generate scatter plot for top 25 teams (adjusted win%% vs SOS)')
    
    args = parser.parse_args()
    
    # Set the global year variable based on CLI argument
    global year
    year = args.year
    
    schedule = get_schedule(update=args.update)
    teams = get_teams(schedule)
    fbs_schedule = filter_schedule_fbs_only(schedule, teams)
    
    if args.compare:
        # Generate rankings first to get rank information
        rankings = get_rankings(fbs_schedule, teams, create_plot=False)
        print("\n" + "="*50)
        # Then compare the two teams
        compare_teams(fbs_schedule, args.compare[0], args.compare[1], rankings)
    elif args.team:
        # Generate rankings first to get rank information
        rankings = get_rankings(fbs_schedule, teams, create_plot=args.plot)
        print("\n" + "="*50)
        # Then analyze the specific team
        get_team_schedule(fbs_schedule, args.team, rankings)
    else:
        rankings = get_rankings(fbs_schedule, teams, create_plot=args.plot)


if __name__ == "__main__":
    main()
