from src.rankings.build import get_schedule, get_teams, filter_schedule_fbs_only, get_rankings
import src.rankings.build as build

build.year = 2025
schedule = get_schedule(update=False)
teams = get_teams(schedule)
fbs_schedule = filter_schedule_fbs_only(schedule, teams)
rankings = get_rankings(fbs_schedule, teams, create_plot=False)

print('\nOklahoma vs Alabama ranking check:')
for team in ['Oklahoma', 'Alabama']:
    if team in rankings:
        rank = rankings[team]
        print(f'{rank:2d}. {team:15}')