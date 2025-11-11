# Fantasy Basketball Stats Predictor 🏀

**Fantasy Basketball Stats Predictor** is a command-line tool that fetches live NBA player data and team schedules using the `nba_api`, projects player stats for the selected week, and compares fantasy teams.

---

## Features

- Lookup NBA players by full or partial name.
- Calculate season averages from game logs.
- Project weekly totals based on team schedules.
- Compare two fantasy teams category-by-category.
- Supports current week and next week projections.
- Aggregates team stats including FG% and FT%.

---

## Installation

1. Clone this repository:

```bash
https://github.com/tonywang0907/fantasy_basketball_stats_predictor.git
cd fantasy_basketball_stats_predictor
```

2. Install the required Python packages:

```bash 
pip install nba_api pandas requests
```
- nba_api – Fetch NBA player stats.
- pandas – Handle and compute game logs.
- requests – Fetch NBA schedule data.
---

## Usage 
Run the main script and follow the command-line instructions:

```bash 
python main.py
```

- Choose 1 to calculate stats for your own roster.
- Choose 2 to compare two fantasy teams.
- Enter player names when prompted (comma-separated).
- Select the week (current or next) for projections.
- Follow on-screen prompts to view averages and projections.
- You can type quit at any input prompt to exit the program.

---

## Example

```bash
🏀 Welcome to Fantasy Scheduler!
1️⃣ Calculate your own roster stats
2️⃣ Compare two fantasy teams
Select option (1 or 2): 1
Select week (1 = current, 2 = next): 2
Enter Your roster players (comma-separated): LeBron James, Stephen Curry
...
📊 LeBron James - 2025-26 Season Averages
PTS     : 27.45
REB     : 7.89
...
```
