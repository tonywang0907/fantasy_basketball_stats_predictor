"""
🏀 Fantasy Scheduler — NBA Weekly Projection Tool
------------------------------------------------
Fetches live NBA player data and team schedules using `nba_api`,
projects player stats for the selected week, and compares fantasy teams.

Author: [Tony Wang]
Version: 1.0
Date: 2025-11-11
"""

from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import playergamelog, commonplayerinfo

import pandas as pd
import requests
from datetime import datetime, date, timedelta

# ==========================================================
# 🔹 PLAYER & TEAM LOOKUP HELPERS
# ==========================================================

def find_player_id(player_name: str):
    """
    Find an exact player match and return their NBA player ID.

    Args:
        player_name (str): Full name of the player (e.g., "LeBron James").

    Returns:
        int | None: Player ID if found, otherwise None.
    """

    player_data = players.find_players_by_full_name(player_name)
    if not player_data:
        return None

    for p in player_data:
        if p["full_name"].lower() == player_name.lower():
            return p["id"]  # return ID immediately if match found

    return None  # no match found

def find_player_fuzzy(input_name: str):
    """
    Return a list of possible players matching part of a name (case-insensitive).

    Args:
        input_name (str): Partial or full name to search.

    Returns:
        list[dict]: List of matching player dicts, each containing:
            {"name": full name, "id": player ID}.
    """
    candidates = []
    input_lower = input_name.lower()
    for p in players.get_players():
        if input_lower in p["full_name"].lower():
            candidates.append({"name": p["full_name"], "id": p["id"]})
    return candidates

# Ask user to pick the correct player if multiple candidates exist
def choose_player(candidates):
    """
    Let the user choose a player from a list of candidates.

    Args:
        candidates (list[dict]): List of {"name": str, "id": int} player options.

    Returns:
        dict | None: Selected player dictionary, or None if no valid choice.
    """
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]

    print("Multiple players found. Please choose:")
    for i, p in enumerate(candidates, 1):
        print(f"{i}. {p['name']}")

    while True:
        choice = input(f"Enter number (1-{len(candidates)}): ").strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(candidates):
                return candidates[idx]
        print("Invalid choice. Try again.")

def get_player_team_id(player_id: int):
    """
    Retrieve a player's current team ID.

    Args:
        player_id (int): NBA player ID.

    Returns:
        int: Team ID.
    """
    info = commonplayerinfo.CommonPlayerInfo(player_id=player_id)
    df = info.get_data_frames()[0]
    return int(df.loc[0, "TEAM_ID"])

# ==========================================================
# 🔹 STATS FETCHING & AVERAGE CALCULATIONS
# ==========================================================

def print_stats(title: str, stats: dict, extra_info: str = None):
    """
    Print any stats dictionary in a formatted table.
    Percentages are handled automatically.
    """
    print(f"\n{title}\n")
    if extra_info:
        print(extra_info + "\n")
    for stat, val in stats.items():
        if "PCT" in stat:
            print(f"{stat:<8}: {val:.1f}%")
        else:
            print(f"{stat:<8}: {val:.2f}")
    print("\n" + "-"*40 + "\n")


def get_player_gamelog(player_id: int, season: str = "2025-26") -> pd.DataFrame:
    """
    Fetch a player's full game log for a season.

    Args:
        player_id (int): NBA player ID.
        season (str): Season string, e.g., "2025-26".

    Returns:
        pd.DataFrame: Game-by-game stats for that season.
    """
    game_log = playergamelog.PlayerGameLog(player_id=player_id, season=season)
    return game_log.get_data_frames()[0]


def calculate_accurate_averages(df: pd.DataFrame) -> dict:
    """
    Calculate per-game averages and accurate FG%/FT% from a player's game log.

    Args:
        df (pd.DataFrame): Player's game log dataframe.

    Returns:
        dict: Average stats and shooting percentages.
    """
    total_fgm, total_fga = df["FGM"].sum(), df["FGA"].sum()
    total_ftm, total_fta = df["FTM"].sum(), df["FTA"].sum()

    fg_pct = (total_fgm / total_fga * 100) if total_fga > 0 else 0
    ft_pct = (total_ftm / total_fta * 100) if total_fta > 0 else 0

    averages = {
        "PTS": df["PTS"].mean(),
        "REB": df["REB"].mean(),
        "AST": df["AST"].mean(),
        "STL": df["STL"].mean(),
        "BLK": df["BLK"].mean(),
        "TOV": df["TOV"].mean(),
        "FG3M": df["FG3M"].mean(),
        "FGA": df["FGA"].mean(),   # <-- add this
        "FGM": df["FGM"].mean(),   # <-- add this
        "FTA": df["FTA"].mean(),   # <-- add this
        "FTM": df["FTM"].mean(),   # <-- add this
        "FG_PCT": fg_pct,
        "FT_PCT": ft_pct,
    }

    return averages

def display_player_averages(player_name: str, averages: dict, season: str):
    """
    Display a formatted summary of a player's season averages.

    Args:
        player_name (str): Full player name.
        averages (dict): Player averages dictionary.
        season (str): Season string.
    """
    print(f"\n📊 {player_name} - {season} Season Averages:\n")
    for stat, val in averages.items():
        if "PCT" in stat:
            print(f"{stat:<8}: {val:.1f}%")
        else:
            print(f"{stat:<8}: {val:.2f}")
    print("\n" + "-" * 40 + "\n")

# ==========================================================
# 🔹 SCHEDULE UTILITIES
# ==========================================================

def load_full_schedule():
    """
    Load the full NBA schedule from the official JSON feed.

    Returns:
        dict: Complete NBA schedule data.
    """
    url = "https://cdn.nba.com/static/json/staticData/scheduleLeagueV2_1.json"
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json()

def count_team_games_for_week(team_id: int, start_date: date, end_date: date, schedule: dict):
    """
    Count how many games a team plays between two dates using preloaded schedule.

    Args:
        team_id (int): Team ID.
        start_date (date): Start of week.
        end_date (date): End of week.
        schedule (dict): Preloaded NBA schedule data.

    Returns:
        int: Number of games scheduled.
    """
    count = 0
    for date_entry in schedule["leagueSchedule"]["gameDates"]:
        game_date = datetime.strptime(date_entry["gameDate"], "%m/%d/%Y %H:%M:%S").date()
        if start_date <= game_date <= end_date:
            for game in date_entry["games"]:
                if int(game["homeTeam"]["teamId"]) == team_id or int(game["awayTeam"]["teamId"]) == team_id:
                    count += 1
    return count


def get_week_range(option=1):
    """
    Get date range for current or next week.

    Args:
        option (int): 1 for current week, 2 for next week.

    Returns:
        tuple[date, date]: (start_date, end_date)
    """
    today = date.today()
    
    if option == 1:  # current week
        start = today
        end = today + timedelta(days=(6 - today.weekday()))
    elif option == 2:  # next week
        days_until_next_monday = (7 - today.weekday()) % 7
        if days_until_next_monday == 0:
            days_until_next_monday = 7
        start = today + timedelta(days=days_until_next_monday)
        end = start + timedelta(days=6)
    else:
        raise ValueError("Option must be 1 (current) or 2 (next)")
        
    return start, end

# ==========================================================
# 🔹 PROJECTIONS & AGGREGATIONS
# ==========================================================

def project_weekly_totals(averages: dict, num_games: int) -> dict:
    """
    Project a player's weekly totals by scaling per-game averages.

    Args:
        averages (dict): Player's per-game averages.
        num_games (int): Number of games in the week.

    Returns:
        dict: Projected totals for the week.
    """
    projected = {}

    # Scale counting stats by number of games
    for stat, val in averages.items():
        if stat not in ["FG_PCT", "FT_PCT"]:
            projected[stat] = val * num_games

    # Keep percentages the same (they don’t scale)
    projected["FG_PCT"] = averages.get("FG_PCT", 0)
    projected["FT_PCT"] = averages.get("FT_PCT", 0)

    return projected

def aggregate_projected_totals(all_projected: list) -> dict:
    """
    Combine multiple players' projected stats into team totals.

    FG% and FT% are recalculated from combined FGM/FGA and FTM/FTA.

    Args:
        all_projected (list[dict]): List of player projections.

    Returns:
        dict: Aggregated totals and accurate team shooting percentages.
    """
    total = {}
    total_fgm = total_fga = total_ftm = total_fta = 0

    for proj in all_projected:
        for stat, val in proj.items():
            if stat == "FGM":
                total_fgm += val
            elif stat == "FGA":
                total_fga += val
            elif stat == "FTM":
                total_ftm += val
            elif stat == "FTA":
                total_fta += val
            elif stat not in ["FG_PCT", "FT_PCT"]:
                total[stat] = total.get(stat, 0) + val

    # Save raw totals
    total["FGM"] = total_fgm
    total["FGA"] = total_fga
    total["FTM"] = total_ftm
    total["FTA"] = total_fta

    # Compute accurate team percentages
    total["FG_PCT"] = (total_fgm / total_fga * 100) if total_fga > 0 else 0
    total["FT_PCT"] = (total_ftm / total_fta * 100) if total_fta > 0 else 0

    return total

# ==========================================================
# 🔹 ROSTER & TEAM COMPARISON LOGIC
# ==========================================================

def input_roster(team_label="Team"):
    """
    Prompt user to enter a roster of players.

    Args:
        team_label (str): Label for prompt (e.g., "Team A").

    Returns:
        list[str]: List of player names.
    """
    roster_input = input(f"Enter {team_label} players (comma-separated): ").strip()
    return [name.strip() for name in roster_input.split(",")]


def display_projected_totals(player_name: str, projected: dict, num_games: int, start: date, end: date):
    """
    Display a player's projected totals for the given week.

    Args:
        player_name (str): Full player name.
        projected (dict): Projected weekly totals.
        num_games (int): Number of games scheduled.
        start (date): Start date of the week.
        end (date): End date of the week.
    """
    print(f"\n📈 Estimated totals for {player_name} over {num_games} games ({start} to {end}):\n")
    for stat, val in projected.items():
        if "PCT" in stat:
            print(f"{stat:<8}: {val:.1f}%")
        else:
            print(f"{stat:<8}: {val:.2f}")
    print("\n" + "-" * 40 + "\n")

def process_roster(player_names, week_option=1, schedule_data=None):
    """
    Process and project stats for a list of players over a given week.
    Optimized: schedule is fetched once and passed in.

    Args:
        player_names (list[str]): List of player names.
        week_option (int): 1 = current week, 2 = next week.
        schedule_data (dict, optional): Preloaded schedule to avoid repeated API calls.

    Returns:
        tuple: (all_projected list, aggregated totals dict)
    """
    start, end = get_week_range(week_option)
    if schedule_data is None:
        schedule_data = load_full_schedule()  # fetch once

    all_projected = []

    for name in player_names:
        selected_player = None
        while not selected_player:
            print(f"\n🔹 Processing '{name}'...\n")
            candidates = find_player_fuzzy(name)
            if not candidates:
                name = input(f"❌ No players found for '{name}'. Retype: ").strip()
                continue
            selected_player = choose_player(candidates)

        player_id = selected_player["id"]
        full_name = selected_player["name"]
        season = "2025-26"
        df = get_player_gamelog(player_id, season)

        if df.empty:
            print(f"⚠️ No game data for {full_name}. Projected stats will be 0.\n")
            averages = {k: 0 for k in ["PTS","REB","AST","STL","BLK","TOV","FG3M",
                                        "FGA","FGM","FTA","FTM","FG_PCT","FT_PCT"]}
        else:
            averages = calculate_accurate_averages(df)

        print_stats(f"📊 {full_name} - {season} Season Averages", averages)

        team_id = get_player_team_id(player_id)
        games = count_team_games_for_week(team_id, start, end, schedule_data)
        projected = project_weekly_totals(averages, games)
        all_projected.append(projected)

        print_stats(f"📈 {full_name} - Projected totals ({games} games)", projected,
                    f"📅 {full_name}'s team will play {games} games from {start} to {end}")

    aggregated = aggregate_projected_totals(all_projected) if all_projected else {}

    return all_projected, aggregated

def compare_two_teams(team_a_names, team_b_names, week_option=1):
    """
    Compare two fantasy teams' weekly projections category-by-category.

    Args:
        team_a_names (list[str]): Team A player names.
        team_b_names (list[str]): Team B player names.
        week_option (int): 1 = current week, 2 = next week.

    Returns:
        tuple: (team_a_totals, team_b_totals, overall_winner)
    """
    _, team_a_totals = process_roster(team_a_names, week_option)
    _, team_b_totals = process_roster(team_b_names, week_option)

    categories = ["PTS","REB","AST","STL","BLK","TOV","FG3M"]
    team_a_score = 0
    team_b_score = 0

    print("\n📊 Fantasy Team Comparison (Projected Totals):\n")
    for stat in categories:
        a_val = team_a_totals.get(stat,0)
        b_val = team_b_totals.get(stat,0)

        if stat == "TOV":  # fewer turnovers is better
            winner = "Team A" if a_val < b_val else ("Team B" if b_val < a_val else "Tie")
        else:
            winner = "Team A" if a_val > b_val else ("Team B" if b_val > a_val else "Tie")

        if winner == "Team A":
            team_a_score += 1
        elif winner == "Team B":
            team_b_score += 1

        print(f"{stat:<5}: Team A: {a_val:.2f} | Team B: {b_val:.2f} → {winner}")

    # FG% and FT%
    print(f"FG% : Team A: {team_a_totals.get('FG_PCT',0):.1f}% | Team B: {team_b_totals.get('FG_PCT',0):.1f}%")
    print(f"FT% : Team A: {team_a_totals.get('FT_PCT',0):.1f}% | Team B: {team_b_totals.get('FT_PCT',0):.1f}%")


    # Determine overall winner
    if team_a_score > team_b_score:
        overall_winner = "Team A"
    elif team_b_score > team_a_score:
        overall_winner = "Team B"
    else:
        overall_winner = "Tie"

    print(f"\n🏆 Weekly winner: {overall_winner}\n")
    return team_a_totals, team_b_totals, overall_winner


def safe_input(prompt: str):
    """
    Wrap input() so that typing 'q' or 'quit' exits the program cleanly.
    """
    user_input = input(prompt).strip()
    if user_input.lower() in ("q", "quit"):
        print("👋 Exiting Fantasy Scheduler. Goodbye!")
        exit(0)  # exits the program
    return user_input

# ==========================================================
# 🔹 MAIN ENTRY POINT
# ==========================================================

def main():
    print("🏀 Welcome to Fantasy Scheduler!\n")
    print("1️⃣ Calculate your own roster stats")
    print("2️⃣ Compare two fantasy teams")
    choice = safe_input("Select option (1 or 2, or 'q' to quit): ")

    week_option = safe_input("Select week (1 = current, 2 = next, or 'q' to quit): ")
    week_option = int(week_option) if week_option in ["1","2"] else 1

    if choice == "1":
        player_names = safe_input("Enter your roster (comma-separated, or 'q' to quit): ")
        _, aggregated = process_roster(player_names, week_option)
        if aggregated:
            print_stats("🏆 Aggregated stats for your roster", aggregated)

    elif choice == "2":
        team_a_names = input_roster("Team A")
        team_b_names = input_roster("Team B")
        compare_two_teams(team_a_names, team_b_names, week_option)

    else:
        print("❌ Invalid option.")


if __name__ == "__main__":
    main()