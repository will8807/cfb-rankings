from src.rankings.build import get_schedule, get_teams, filter_schedule_fbs_only, get_rankings

# Set up the data for 2025
import src.rankings.build as build
build.year = 2025

schedule = get_schedule(update=False)
teams = get_teams(schedule)
fbs_schedule = filter_schedule_fbs_only(schedule, teams)
rankings = get_rankings(fbs_schedule, teams, create_plot=False)

print("2025 College Football Rankings")
print("=" * 60)
print(f"Rankings type: {type(rankings)}")
if isinstance(rankings, list):
    for i, team in enumerate(rankings[:25]):
        print(f"{i+1:2d}. {team['team']:25} {team['wins']}-{team['losses']} (Adj: {team['adjusted_win_pct']:.3f})")
else:
    print("Rankings is not a list, investigating further...")