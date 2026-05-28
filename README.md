# Coach IA — asistente táctico multi-agente para fútbol

Proyecto final del curso Introducción a la Inteligencia Artificial (EAFIT, 2026).

Le das al sistema un rival de La Liga 2025-26 y tu equipo, y te devuelve un informe de scouting, una alineación de once jugadores con su formación, y tres instrucciones tácticas. Todo sale de datos reales de la temporada, no de la memoria del modelo.

El anteproyecto original (Fase 1) está en [`docs/anteproyecto.md`](docs/anteproyecto.md). Este README documenta lo que terminó construido, que se desvió del plan en dos puntos importantes (ver [Qué cambió respecto al plan](#qué-cambió-respecto-al-plan)).

**Equipo:** David Elias Franco, Miguel Angel Montoya, Daniel Sidney Curelop.

---

## Cómo funciona

Dos agentes que se pasan el trabajo, coordinados por un grafo de LangGraph:

```
   rival + tu equipo
        │
        ▼
   ┌─────────┐   informe de       ┌─────────┐
   │  SCOUT  │ ─── scouting ────▶ │  COACH  │ ──▶  XI + formación
   └─────────┘                    └─────────┘       + 3 instrucciones
   lee datos del rival            lee tu plantilla
   (perfil, últimos partidos)     y tus alineaciones recientes
```

El **Scout** estudia al rival y escribe un informe. El **Coach** recibe ese informe y arma el plan de partido. La gracia es que el Coach no repite el análisis del rival: lo usa como punto de partida. Eso es lo que lo hace un sistema multi-agente y no dos modelos sueltos.

Cada agente es Claude Haiku 4.5 con herramientas que consultan los CSVs de datos. Los agentes no inventan estadísticas: tienen que llamar a una herramienta para obtenerlas.

---

## Estructura del repo

```
coach-ia/
├── src/
│   ├── data/              # bajan los datos a CSV
│   │   ├── fetch.py          stats de Understat (xG, PPDA, ...)
│   │   └── fetch_lineups.py  alineaciones reales de ESPN
│   ├── agents/
│   │   ├── scout/         # agente que perfila al rival (2 tools)
│   │   └── coach/         # agente que arma el plan (3 tools)
│   ├── graph.py           # orquestador: scout → coach
│   └── evals/             # suite de evaluación (6 módulos)
├── notebooks/
│   ├── 01_eda.ipynb           exploración de datos + umbrales
│   └── 02_eval_results.ipynb  análisis de la corrida de eval
├── scripts/
│   └── comparar_corridas.py   compara dos corridas (v1 vs v2)
├── data/processed/        # los 6 CSVs ya descargados (versionados)
├── evals/results/         # resultados de la eval (versionados)
└── docs/anteproyecto.md   # entregable de Fase 1
```

---

## Stack

| Pieza | Qué se usó |
|---|---|
| Orquestación | LangGraph (grafo `scout → coach`) |
| Agentes | Claude Haiku 4.5 (`claude-haiku-4-5-20251001`) |
| Juez de la eval | Claude Sonnet 4.6 (`claude-sonnet-4-6`), un modelo más capaz que el evaluado |
| Datos de stats | Understat vía `soccerdata` (xG, xA, PPDA, deep completions) |
| Datos de alineaciones | ESPN vía `soccerdata` |

---

## Cómo correr

La instalación paso a paso está en [`SETUP.md`](SETUP.md). Resumido: creas un venv, instalas `requirements.txt` y pones tu `ANTHROPIC_API_KEY` en un archivo `.env`.

Los datos ya vienen descargados en `data/processed/`, así que puedes saltarte el paso de descarga. Si quieres regenerarlos:

```bash
.venv/bin/python -m src.data.fetch            # stats de Understat → 4 CSVs
.venv/bin/python -m src.data.fetch_lineups    # alineaciones de ESPN (380 partidos, ~30 min)
```

Correr el sistema completo para un partido:

```bash
.venv/bin/python -m src.graph                 # Villarreal vs Atlético (editable en el archivo)
```

Probar cada agente por separado:

```bash
.venv/bin/python -m src.agents.scout.agent    # solo el scouting del rival
.venv/bin/python -m src.agents.coach.agent    # solo el plan del Coach
```

Correr la evaluación:

```bash
.venv/bin/python -m src.evals.run --smoke     # 3 partidos (prueba rápida)
.venv/bin/python -m src.evals.run             # los 30 partidos (~25 min)
```

> **Nota para el equipo de documentación:** correr los agentes y la eval necesita una `ANTHROPIC_API_KEY`. Si no tienen una, los resultados de la última corrida ya están en `evals/results/` y los notebooks los leen sin necesidad de re-ejecutar nada.

---

## Resultados

Evaluación sobre 30 partidos estratificados (10 de la parte alta de la tabla, 10 del medio, 10 de abajo). Dos tipos de métrica:

**Estructuradas** (contra la alineación real que puso el DT):
- `lineup_overlap`: fracción de los 11 propuestos que sí jugaron de titulares.
- `formation_match`: si la formación propuesta coincide con la real.

**Cualitativas** (juez LLM, escala 0-5):
- `tactical_coherence`, `specificity`, `faithfulness` (si el plan inventa datos o se ciñe a lo que dicen las herramientas).

El hallazgo más interesante salió de comparar dos versiones del prompt del Coach. En la primera, el Coach alineó a Piqué (retirado en 2022) en el Barcelona. Reforzamos el prompt para prohibir citar jugadores que no estén en las herramientas, volvimos a correr, y ese caso pasó de 2.0 a 5.0 en `faithfulness`. Pero a cambio el sistema se volvió más cauto y las notas promedio bajaron un poco. Ese intercambio, medido con números, está en `notebooks/02_eval_results.ipynb` y se reproduce con:

```bash
.venv/bin/python scripts/comparar_corridas.py
```

| Métrica | v1 | v2 (anti-alucinación) |
|---|---|---|
| lineup_overlap | 0.60 | 0.58 |
| formation_match | 0.47 | 0.37 |
| tactical_coherence | 4.04 | 3.83 |
| specificity | 4.32 | 4.10 |
| faithfulness | 3.54 | 3.17 |

**Limitación metodológica:** el juez solo ve el informe del Scout y el plan del Coach, no las herramientas que el Coach llamó. Así que `faithfulness` mide adherencia al scouting, no a la realidad completa de los datos.

---

## Qué cambió respecto al plan

El anteproyecto planeaba dos cosas que no sobrevivieron al contacto con la realidad:

1. **Datos: FBref → Understat + ESPN.** FBref está detrás de Cloudflare y bloqueó el scraper aunque usáramos navegador real. Understat no tiene esa protección y además trae métricas más ricas para análisis táctico (xg_chain, xg_buildup, PPDA). Las alineaciones reales, que Understat no da, salen de ESPN.

2. **Modelo: Gemini 2.0 Flash → Claude Haiku 4.5.** El proyecto de Google que teníamos no tenía cuota de free tier para Gemini (devolvía `limit: 0`). Claude Haiku, que el anteproyecto ya listaba como alternativa de respaldo, pasó a ser el modelo de producción.

---

## Apéndice — Declaración de uso de IA

Para la redacción de la documentación se usó IA generativa como apoyo. Las decisiones técnicas y la validación del código y los resultados fueron del equipo.
