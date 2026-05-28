"""Descarga alineaciones desde ESPN para La Liga 25-26 → data/processed/lineups.csv

Uso:
    python -m src.data.fetch_lineups                  # baja las 380 alineaciones
    python -m src.data.fetch_lineups --tail 30        # solo los 30 partidos más recientes
    python -m src.data.fetch_lineups --head 10        # solo los 10 primeros (debug)
"""
import argparse
from pathlib import Path

import pandas as pd
import soccerdata as sd

LEAGUE = "ESP-La Liga"
SEASON = "2526"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "processed"


def main(head: int | None, tail: int | None) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    espn = sd.ESPN(leagues=LEAGUE, seasons=SEASON)

    schedule = espn.read_schedule()
    print(f"ESPN schedule: {len(schedule)} partidos")

    sched_sorted = schedule.sort_values("date")
    if tail is not None:
        sched_sorted = sched_sorted.tail(tail)
        print(f"Bajando los {tail} partidos más recientes")
    elif head is not None:
        sched_sorted = sched_sorted.head(head)
        print(f"Bajando los {head} primeros partidos")

    match_ids = sched_sorted["game_id"].astype(int).tolist()

    print(f"Pidiendo alineaciones de {len(match_ids)} partidos...")
    lineups = espn.read_lineup(match_id=match_ids)

    schedule.to_csv(OUT / "espn_schedule.csv")
    lineups.to_csv(OUT / "lineups.csv")

    print(f"espn_schedule: {len(schedule)} filas  → {OUT / 'espn_schedule.csv'}")
    print(f"lineups:       {len(lineups)} filas  → {OUT / 'lineups.csv'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--tail", type=int, help="Solo los N partidos más recientes")
    group.add_argument("--head", type=int, help="Solo los N primeros partidos")
    args = parser.parse_args()
    main(args.head, args.tail)
