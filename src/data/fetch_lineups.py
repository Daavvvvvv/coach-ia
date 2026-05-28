"""Descarga alineaciones desde ESPN para La Liga 25-26 → data/processed/lineups.csv

Uso:
    python -m src.data.fetch_lineups                 # baja las 380 alineaciones
    python -m src.data.fetch_lineups --limit 10      # solo primeras 10 (smoke test)
"""
import argparse
from pathlib import Path

import soccerdata as sd

LEAGUE = "ESP-La Liga"
SEASON = "2526"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "processed"


def main(limit: int | None) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    espn = sd.ESPN(leagues=LEAGUE, seasons=SEASON)

    schedule = espn.read_schedule()
    print(f"ESPN schedule: {len(schedule)} partidos")

    match_ids = schedule["game_id"].astype(int).tolist()
    if limit is not None:
        match_ids = match_ids[:limit]
        print(f"Bajando solo {limit} partidos (modo prueba)")

    print(f"Pidiendo alineaciones de {len(match_ids)} partidos...")
    lineups = espn.read_lineup(match_id=match_ids)

    schedule.to_csv(OUT / "espn_schedule.csv")
    lineups.to_csv(OUT / "lineups.csv")

    print(f"espn_schedule: {len(schedule)} filas  → {OUT / 'espn_schedule.csv'}")
    print(f"lineups:       {len(lineups)} filas  → {OUT / 'lineups.csv'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limita a los primeros N partidos (para pruebas; sin flag baja todo)",
    )
    args = parser.parse_args()
    main(args.limit)
