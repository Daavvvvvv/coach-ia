"""Runner principal de la suite de evaluación.

Uso:
    python -m src.evals.run --smoke     # 3 partidos, uno por tier
    python -m src.evals.run              # los 30 partidos
"""
import argparse
import json
import time
from datetime import datetime
from pathlib import Path

import pandas as pd

from src.evals.extract import extract_plan
from src.evals.judge import judge_plan
from src.evals.metrics import actual_starting_xi, formation_match, lineup_overlap
from src.evals.sampler import stratified_sample
from src.graph import build_graph

ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = ROOT / "evals" / "results"


def evaluate_one(graph, row: pd.Series) -> dict:
    """Corre el pipeline completo para un partido."""
    out = {
        "tier": row["tier"],
        "our_team": row["our_team"],
        "opponent": row["opponent"],
        "date": row["date"],
        "game": row["game"],
        "error": "",
    }
    try:
        result = graph.invoke({"our_team": row["our_team"], "opponent": row["opponent"]})
        scouting = result["scouting"]
        plan_text = result["plan"]
        out["scouting"] = scouting
        out["plan_text"] = plan_text
    except Exception as e:
        out["error"] = f"graph: {e}"
        return out

    try:
        plan = extract_plan(plan_text)
        out["xi_proposed"] = json.dumps(plan.xi, ensure_ascii=False)
        out["formation_proposed"] = plan.formation
        out["instructions"] = json.dumps(plan.instructions, ensure_ascii=False)
    except Exception as e:
        out["error"] = f"extract: {e}"
        return out

    actual = actual_starting_xi(row["our_team"], row["date"])
    if actual is None:
        out["lineup_overlap"] = None
        out["formation_match"] = None
        out["formation_actual"] = None
        out["xi_actual"] = None
    else:
        actual_xi, actual_form = actual
        out["xi_actual"] = json.dumps(actual_xi, ensure_ascii=False)
        out["formation_actual"] = actual_form
        out["lineup_overlap"] = round(lineup_overlap(plan, actual_xi), 3)
        out["formation_match"] = formation_match(plan, actual_form)

    try:
        verdict = judge_plan(plan, scouting, row["our_team"], row["opponent"])
        out["tactical_coherence"] = verdict.tactical_coherence.score
        out["tactical_coherence_why"] = verdict.tactical_coherence.rationale
        out["specificity"] = verdict.specificity.score
        out["specificity_why"] = verdict.specificity.rationale
        out["faithfulness"] = verdict.faithfulness.score
        out["faithfulness_why"] = verdict.faithfulness.rationale
    except Exception as e:
        out["error"] = f"judge: {e}"

    return out


def main(smoke: bool) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    sample = stratified_sample()
    if smoke:
        sample = (
            pd.concat([sample[sample["tier"] == t].head(1) for t in ("top", "mid", "bottom")])
            .reset_index(drop=True)
        )
        print(f"Modo smoke: {len(sample)} partidos")
    else:
        print(f"Modo full: {len(sample)} partidos")

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = "smoke" if smoke else "full"
    out_path = RESULTS_DIR / f"results_{suffix}_{stamp}.csv"
    print(f"Checkpoint en: {out_path}")

    graph = build_graph()
    rows = []
    t0 = time.time()
    for i, row in sample.iterrows():
        print(f"[{i + 1}/{len(sample)}] {row['tier']:6s} | {row['our_team']} vs {row['opponent']}  ({row['date']})")
        t_start = time.time()
        rows.append(evaluate_one(graph, row))
        pd.DataFrame(rows).to_csv(out_path, index=False)
        print(f"          ↳ {time.time() - t_start:.1f}s")

    df = pd.DataFrame(rows)
    print(f"\nGuardado: {out_path}")
    print(f"Total: {time.time() - t0:.1f}s\n")

    metric_cols = [
        "lineup_overlap",
        "formation_match",
        "tactical_coherence",
        "specificity",
        "faithfulness",
    ]
    print("=== Resumen ===")
    print(df[metric_cols].describe().round(2).to_string())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true", help="3 partidos (1 por tier) en lugar de los 30")
    args = parser.parse_args()
    main(args.smoke)
