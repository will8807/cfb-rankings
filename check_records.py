import pandas as pd

df = pd.read_csv('data/schedule_2025.csv')

# Check the actual records for the teams mentioned
teams_to_check = ['Ohio State', ' Ohio State', 'Indiana', ' Indiana', 'Mississippi', ' Mississippi']

for team in teams_to_check:
    wins = len(df[df['Winner'] == team])
    losses = len(df[df['Loser'] == team])
    if wins > 0 or losses > 0:
        print(f"'{team}': {wins}-{losses}")

# Show any losses for Ohio State variants
print("\nOhio State losses:")
osu_losses = df[df['Loser'].str.contains('Ohio State', na=False)]
for _, game in osu_losses.iterrows():
    print(f"  Week {game['Wk']}: Lost to {game['Winner']}")

print("\nIndiana losses:")  
ind_losses = df[df['Loser'].str.contains('Indiana', na=False)]
for _, game in ind_losses.iterrows():
    print(f"  Week {game['Wk']}: Lost to {game['Winner']}")