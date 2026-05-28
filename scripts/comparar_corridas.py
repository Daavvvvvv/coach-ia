"""Imprime la comparación v1 vs v2 de las dos últimas corridas full de la eval.

Pensado para mostrar en pantalla (video / documentación): medias por métrica,
delta entre corridas, y el caso 'Piqué' (Espanyol vs Barcelona) que pasó de
2.0 a 5.0 en faithfulness tras reforzar el prompt del Coach.

Uso:
    python scripts/comparar_corridas.py
"""
import glob
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "evals" / "results"

METRICS = ["lineup_overlap", "formation_match", "tactical_coherence", "specificity", "faithfulness"]


def main() -> None:
    runs = sorted(glob.glob(str(RESULTS / "results_full_*.csv")))
    if len(runs) < 2:
        print("Hacen falta al menos 2 corridas full para comparar.")
        return

    v1 = pd.read_csv(runs[-2])
    v2 = pd.read_csv(runs[-1])

    print("=" * 56)
    print("  COMPARACIÓN DE CORRIDAS — 30 partidos, mismo seed")
    print("=" * 56)
    print(f"  v1 (prompt base):     {Path(runs[-2]).name}")
    print(f"  v2 (anti-alucinación): {Path(runs[-1]).name}")
    print()

    comp = pd.DataFrame({
        "v1": v1[METRICS].mean().round(2),
        "v2": v2[METRICS].mean().round(2),
    })
    comp["Δ"] = (comp["v2"] - comp["v1"]).round(2)
    print(comp.to_string())

    print()
    print("-" * 56)
    print("  CASO 'PIQUÉ' — Espanyol vs Barcelona")
    print("-" * 56)
    r1 = v1[(v1["our_team"] == "Espanyol") & (v1["opponent"] == "Barcelona")].iloc[0]
    r2 = v2[(v2["our_team"] == "Espanyol") & (v2["opponent"] == "Barcelona")].iloc[0]
    print(f"  faithfulness:  v1 = {r1.faithfulness}   →   v2 = {r2.faithfulness}")
    print()
    print(f"  v1: {str(r1.faithfulness_why)[:260]}")
    print()
    print(f"  v2: {str(r2.faithfulness_why)[:260]}")


if __name__ == "__main__":
    main()
