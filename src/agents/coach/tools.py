"""Tools del agente Coach — consultan plantilla, alineaciones recientes y perfil de rival."""
import unicodedata
from pathlib import Path

import pandas as pd
from langchain_core.tools import tool

# Reusamos la tool de perfil de equipo del Scout para que el Coach también pueda leer al rival.
from src.agents.scout.tools import get_team_profile  # noqa: F401  re-exported

ROOT = Path(__file__).resolve().parents[3]
PROC = ROOT / "data" / "processed"

_players = pd.read_csv(PROC / "players.csv")
_lineups = pd.read_csv(PROC / "lineups.csv")
_espn_sched = pd.read_csv(PROC / "espn_schedule.csv")


def _strip(s) -> str:
    """Normaliza nombre: lowercase, sin acentos, sin espacios extra."""
    if pd.isna(s):
        return ""
    n = unicodedata.normalize("NFD", str(s))
    return "".join(c for c in n if unicodedata.category(c) != "Mn").lower().strip()


def _pos_main(p) -> str:
    if pd.isna(p):
        return "?"
    return str(p).strip().split()[0]


def _detect_formation(positions: list[str]) -> str:
    """A partir de los 10 jugadores de campo de ESPN, devuelve formación tipo '4-3-3'."""
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


@tool
def get_team_squad(team: str, min_minutes: int = 500) -> list[dict]:
    """Plantilla regular del equipo: jugadores con minutos >= min_minutes y
    sus estadísticas de Understat (posición agregada, minutos, goles, xG,
    asistencias, xA, shots, key_passes). El agente Coach lo usa para elegir
    quiénes son los regulares y construir la propuesta de XI."""
    target = _strip(team)
    squad = _players[_players["team"].apply(_strip) == target]
    if squad.empty:
        return [{
            "error": f"Equipo no encontrado: {team}",
            "equipos_disponibles": sorted(_players["team"].unique().tolist()),
        }]

    regulars = squad[squad["minutes"] >= min_minutes].sort_values("minutes", ascending=False)
    return [
        {
            "player": r["player"],
            "pos": _pos_main(r["position"]),
            "minutes": int(r["minutes"]),
            "goals": int(r["goals"]),
            "xg": round(float(r["xg"]), 2),
            "assists": int(r["assists"]),
            "xa": round(float(r["xa"]), 2),
            "shots": int(r["shots"]),
            "key_passes": int(r["key_passes"]),
        }
        for _, r in regulars.iterrows()
    ]


@tool
def get_team_recent_lineups(team: str, n: int = 3) -> list[dict]:
    """Últimas N alineaciones titulares del equipo desde ESPN. Devuelve fecha,
    rival, localía, formación detectada (ej. '4-3-3') y los 11 titulares con
    su posición ESPN detallada. Útil para que el Coach respete tendencias
    recientes (qué jugadores y qué dibujo táctico está usando el técnico)."""
    target = _strip(team)
    rows = _lineups[_lineups["team"].apply(_strip) == target]
    if rows.empty:
        return [{
            "error": f"Equipo sin alineaciones disponibles: {team}",
            "equipos_disponibles": sorted(_lineups["team"].unique().tolist()),
        }]

    starters = rows[rows["sub_in"] == "start"]
    out = []
    for game, group in starters.groupby("game"):
        positions = group["position"].tolist()
        sched_row = _espn_sched[_espn_sched["game"] == game]
        if not sched_row.empty:
            sr = sched_row.iloc[0]
            is_home = _strip(sr["home_team"]) == target
            opponent = sr["away_team"] if is_home else sr["home_team"]
            loc = "local" if is_home else "visitante"
        else:
            opponent = "?"
            loc = "?"

        out.append({
            "game": game,
            "rival": opponent,
            "loc": loc,
            "formacion": _detect_formation(positions),
            "titulares": [
                {"player": r["player"], "pos": r["position"]}
                for _, r in group.iterrows()
            ],
        })

    out.sort(key=lambda x: x["game"], reverse=True)
    return out[:n]
