"""Descarga La Liga 2025-26 desde Understat y guarda CSVs en data/processed/."""
from pathlib import Path

import pandas as pd
import soccerdata as sd

LEAGUE = "ESP-La Liga"
SEASON = "2526"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "processed"


def aggregate_teams(team_matches: pd.DataFrame) -> pd.DataFrame:
    """Pasa de un row por partido (home+away) a un row por equipo-temporada."""
    home = pd.DataFrame({
        "team": team_matches["home_team"],
        "points": team_matches["home_points"],
        "xpoints": team_matches["home_expected_points"],
        "gf": team_matches["home_goals"],
        "ga": team_matches["away_goals"],
        "xgf": team_matches["home_xg"],
        "xga": team_matches["away_xg"],
        "np_xgf": team_matches["home_np_xg"],
        "ppda": team_matches["home_ppda"],
        "deep_completions": team_matches["home_deep_completions"],
    })
    away = pd.DataFrame({
        "team": team_matches["away_team"],
        "points": team_matches["away_points"],
        "xpoints": team_matches["away_expected_points"],
        "gf": team_matches["away_goals"],
        "ga": team_matches["home_goals"],
        "xgf": team_matches["away_xg"],
        "xga": team_matches["home_xg"],
        "np_xgf": team_matches["away_np_xg"],
        "ppda": team_matches["away_ppda"],
        "deep_completions": team_matches["away_deep_completions"],
    })
    long = pd.concat([home, away], ignore_index=True)
    teams = long.groupby("team", as_index=False).agg(
        partidos=("points", "count"),
        puntos=("points", "sum"),
        xpuntos=("xpoints", "sum"),
        goles_a_favor=("gf", "sum"),
        goles_en_contra=("ga", "sum"),
        xg_favor=("xgf", "sum"),
        xg_contra=("xga", "sum"),
        np_xg_favor=("np_xgf", "sum"),
        ppda_promedio=("ppda", "mean"),
        deep_completions_total=("deep_completions", "sum"),
    )
    return teams.sort_values("puntos", ascending=False).reset_index(drop=True)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    us = sd.Understat(leagues=LEAGUE, seasons=SEASON)

    players = us.read_player_season_stats()
    team_matches = us.read_team_match_stats()
    matches = us.read_schedule()
    teams = aggregate_teams(team_matches)

    players.to_csv(OUT / "players.csv")
    team_matches.to_csv(OUT / "team_matches.csv")
    matches.to_csv(OUT / "matches.csv")
    teams.to_csv(OUT / "teams.csv", index=False)

    print(f"players:      {len(players)} filas  → {OUT / 'players.csv'}")
    print(f"team_matches: {len(team_matches)} filas  → {OUT / 'team_matches.csv'}")
    print(f"matches:      {len(matches)} filas  → {OUT / 'matches.csv'}")
    print(f"teams:        {len(teams)} filas  → {OUT / 'teams.csv'}")


if __name__ == "__main__":
    main()
