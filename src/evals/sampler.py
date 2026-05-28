"""Muestreo estratificado de 30 partidos: 10 top + 10 mid + 10 bottom."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PROC = ROOT / "data" / "processed"

TIERS = {
    "top": (1, 6),       # posiciones 1-6
    "mid": (7, 14),
    "bottom": (15, 20),
}


def stratified_sample(n_per_tier: int = 10, seed: int = 42) -> pd.DataFrame:
    """Devuelve un DataFrame con columnas: our_team, opponent, date, game, tier."""
    teams = pd.read_csv(PROC / "teams.csv")
    matches = pd.read_csv(PROC / "matches.csv")
    matches["date"] = pd.to_datetime(matches["date"])

    table = teams.sort_values("puntos", ascending=False).reset_index(drop=True)
    table["pos"] = table.index + 1

    rows = []
    for tier, (lo, hi) in TIERS.items():
        tier_teams = table[(table["pos"] >= lo) & (table["pos"] <= hi)]["team"].tolist()

        candidates = matches[
            matches["is_result"]
            & (matches["home_team"].isin(tier_teams) | matches["away_team"].isin(tier_teams))
        ]
        sample = candidates.sample(n=n_per_tier, random_state=seed + lo)

        for _, m in sample.iterrows():
            if m["home_team"] in tier_teams:
                our_team, opponent = m["home_team"], m["away_team"]
            else:
                our_team, opponent = m["away_team"], m["home_team"]
            rows.append({
                "tier": tier,
                "our_team": our_team,
                "opponent": opponent,
                "date": m["date"].date().isoformat(),
                "game": m["game"],
            })

    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = stratified_sample()
    print(f"Total: {len(df)} partidos")
    print()
    print(df.to_string(index=False))
