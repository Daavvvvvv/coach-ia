"""Tools del agente Scout — consultan los CSVs procesados de La Liga 25-26."""
from pathlib import Path

import pandas as pd
from langchain_core.tools import tool

ROOT = Path(__file__).resolve().parents[3]
PROC = ROOT / "data" / "processed"

_teams = pd.read_csv(PROC / "teams.csv")
_matches = pd.read_csv(PROC / "matches.csv")
_matches["date"] = pd.to_datetime(_matches["date"])

# Umbrales calibrados sobre La Liga 25-26 (calculados en notebooks/01_eda.ipynb).
PPDA_Q25 = _teams["ppda_promedio"].quantile(0.25)
PPDA_Q75 = _teams["ppda_promedio"].quantile(0.75)
DC_Q25 = _teams["deep_completions_total"].quantile(0.25)
DC_Q75 = _teams["deep_completions_total"].quantile(0.75)


def _pressure_label(ppda: float) -> str:
    if ppda <= PPDA_Q25:
        return "alta"
    if ppda > PPDA_Q75:
        return "baja"
    return "media"


def _attack_label(dc: float) -> str:
    if dc >= DC_Q75:
        return "dominante"
    if dc < DC_Q25:
        return "limitado"
    return "medio"


@tool
def get_team_profile(team: str) -> dict:
    """Perfil agregado del equipo en La Liga 25-26: puntos, xG a favor y en contra,
    PPDA promedio (intensidad de presión), deep completions (penetración ofensiva),
    y dos etiquetas calibradas sobre la propia temporada: presion (alta/media/baja)
    y ataque (dominante/medio/limitado)."""
    row = _teams[_teams["team"].str.lower() == team.lower()]
    if row.empty:
        return {
            "error": f"Equipo no encontrado: {team}",
            "equipos_disponibles": sorted(_teams["team"].tolist()),
        }
    r = row.iloc[0]
    return {
        "team": r["team"],
        "partidos": int(r["partidos"]),
        "puntos": int(r["puntos"]),
        "xpuntos": round(float(r["xpuntos"]), 1),
        "goles_a_favor": int(r["goles_a_favor"]),
        "goles_en_contra": int(r["goles_en_contra"]),
        "xg_favor": round(float(r["xg_favor"]), 1),
        "xg_contra": round(float(r["xg_contra"]), 1),
        "ppda_promedio": round(float(r["ppda_promedio"]), 2),
        "deep_completions_total": int(r["deep_completions_total"]),
        "presion": _pressure_label(r["ppda_promedio"]),
        "ataque": _attack_label(r["deep_completions_total"]),
    }


@tool
def get_recent_matches(team: str, n: int = 5) -> list[dict]:
    """Devuelve los últimos N partidos jugados del equipo (default 5), con fecha,
    rival, localía, marcador y xG a favor y en contra."""
    team_low = team.lower()
    home = _matches[_matches["home_team"].str.lower() == team_low].copy()
    away = _matches[_matches["away_team"].str.lower() == team_low].copy()

    home["rival"] = home["away_team"]
    home["loc"] = "local"
    home["gf"] = home["home_goals"]
    home["ga"] = home["away_goals"]
    home["xgf"] = home["home_xg"]
    home["xga"] = home["away_xg"]

    away["rival"] = away["home_team"]
    away["loc"] = "visitante"
    away["gf"] = away["away_goals"]
    away["ga"] = away["home_goals"]
    away["xgf"] = away["away_xg"]
    away["xga"] = away["home_xg"]

    all_games = pd.concat([home, away], ignore_index=True)
    all_games = all_games[all_games["is_result"]].sort_values("date", ascending=False).head(n)

    if all_games.empty:
        return [{"error": f"No hay partidos para: {team}"}]

    return [
        {
            "fecha": r["date"].date().isoformat(),
            "rival": r["rival"],
            "loc": r["loc"],
            "marcador": f"{int(r['gf'])}-{int(r['ga'])}",
            "xg_favor": round(float(r["xgf"]), 2),
            "xg_contra": round(float(r["xga"]), 2),
        }
        for _, r in all_games.iterrows()
    ]
