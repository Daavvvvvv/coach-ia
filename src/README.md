# src/

Código del sistema multi-agente.

Estructura prevista:
- `agents/scout.py` — agente Scout (analista del rival).
- `agents/coach.py` — agente Coach (alineación + tácticas).
- `tools/` — `get_team_stats`, `get_recent_matches`, `get_player_stats`, `propose_lineup`.
- `graph.py` — orquestador LangGraph (`START → scout → coach → END`).
- `state.py` — `MessagesState` extendido con `scouting_report` y `final_plan`.
