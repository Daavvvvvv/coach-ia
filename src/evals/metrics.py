"""Métricas estructuradas: lineup_overlap y formation_match."""
import unicodedata
from pathlib import Path

import pandas as pd

from src.evals.schema import CoachPlan

ROOT = Path(__file__).resolve().parents[2]
PROC = ROOT / "data" / "processed"

_lineups = pd.read_csv(PROC / "lineups.csv")
_espn_sched = pd.read_csv(PROC / "espn_schedule.csv")


def _strip(s) -> str:
    if pd.isna(s):
        return ""
    n = unicodedata.normalize("NFD", str(s))
    return "".join(c for c in n if unicodedata.category(c) != "Mn").lower().strip()


def _detect_formation(positions: list[str]) -> str:
    d = m = f = 0
    for p in positions:
        pl = str(p).lower()
        if "goalkeeper" in pl:
            continue
        if "back" in pl or "defender" in pl:
            d += 1
        elif "midfielder" in pl:
            m += 1
        elif "forward" in pl or "striker" in pl:
            f += 1
    return f"{d}-{m}-{f}"


def actual_starting_xi(our_team: str, date: str) -> tuple[list[str], str] | None:
    """Devuelve (lista de 11 nombres titulares, formación detectada) o None si no hay datos."""
    target_team = _strip(our_team)
    target_date = pd.to_datetime(date).date().isoformat()

    sched = _espn_sched.copy()
    sched["date_only"] = pd.to_datetime(sched["date"]).dt.date.astype(str)
    sched_row = sched[
        (sched["date_only"] == target_date)
        & (
            (sched["home_team"].apply(_strip) == target_team)
            | (sched["away_team"].apply(_strip) == target_team)
        )
    ]
    if sched_row.empty:
        return None
    game = sched_row.iloc[0]["game"]

    starters = _lineups[
        (_lineups["game"] == game)
        & (_lineups["team"].apply(_strip) == target_team)
        & (_lineups["sub_in"] == "start")
    ]
    if len(starters) != 11:
        return None

    return starters["player"].tolist(), _detect_formation(starters["position"].tolist())


def lineup_overlap(plan: CoachPlan, actual_xi: list[str]) -> float:
    """Fracción de jugadores propuestos por el Coach que efectivamente fueron titulares."""
    proposed = {_strip(p) for p in plan.xi}
    actual = {_strip(p) for p in actual_xi}
    if not actual:
        return 0.0
    return len(proposed & actual) / 11.0


def formation_match(plan: CoachPlan, actual_formation: str) -> int:
    """1 si la formación propuesta coincide exactamente con la real, 0 si no."""
    return int(plan.formation.strip() == actual_formation.strip())
