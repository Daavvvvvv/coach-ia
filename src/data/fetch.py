"""Descarga La Liga 2025-26 desde FBref y guarda 3 CSVs en data/processed/."""
from pathlib import Path

import soccerdata as sd

LEAGUE = "ESP-La Liga"
SEASON = "2526"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "processed"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fbref = sd.FBref(leagues=LEAGUE, seasons=SEASON)

    teams = fbref.read_team_season_stats(stat_type="standard")
    players = fbref.read_player_season_stats(stat_type="standard")
    matches = fbref.read_schedule()

    teams.to_csv(OUT / "teams.csv")
    players.to_csv(OUT / "players.csv")
    matches.to_csv(OUT / "matches.csv")

    print(f"teams:   {len(teams)} filas  → {OUT / 'teams.csv'}")
    print(f"players: {len(players)} filas  → {OUT / 'players.csv'}")
    print(f"matches: {len(matches)} filas  → {OUT / 'matches.csv'}")


if __name__ == "__main__":
    main()
