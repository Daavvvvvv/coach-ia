"""Orquestador LangGraph: scout → coach.

Estado compartido:
- our_team, opponent: inputs.
- scouting: lo que produce el Scout.
- plan: XI + formación + instrucciones del Coach.
"""
from typing import TypedDict

from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph

from src.agents.coach.agent import build_coach_agent
from src.agents.scout.agent import build_scout_agent

load_dotenv()

_SCOUT = build_scout_agent()
_COACH = build_coach_agent()


class CoachIAState(TypedDict, total=False):
    our_team: str
    opponent: str
    scouting: str
    plan: str


def scout_node(state: CoachIAState) -> dict:
    msg = f"Hazme el scouting del {state['opponent']}."
    result = _SCOUT.invoke({"messages": [{"role": "user", "content": msg}]})
    return {"scouting": result["messages"][-1].content}


def coach_node(state: CoachIAState) -> dict:
    msg = f"""Prepara la alineación de {state['our_team']} para enfrentar a {state['opponent']}.

Aquí tienes el scouting del rival que ya preparó el equipo:

---
{state['scouting']}
---

Usa ese scouting como contexto y sigue llamando a las herramientas para tu propio equipo (plantilla, alineaciones recientes)."""
    result = _COACH.invoke({"messages": [{"role": "user", "content": msg}]})
    return {"plan": result["messages"][-1].content}


def build_graph():
    graph = StateGraph(CoachIAState)
    graph.add_node("scout", scout_node)
    graph.add_node("coach", coach_node)
    graph.add_edge(START, "scout")
    graph.add_edge("scout", "coach")
    graph.add_edge("coach", END)
    return graph.compile()


if __name__ == "__main__":
    g = build_graph()
    result = g.invoke({"our_team": "Villarreal", "opponent": "Atletico Madrid"})
    print("=" * 70)
    print("SCOUTING")
    print("=" * 70)
    print(result["scouting"])
    print()
    print("=" * 70)
    print("PLAN DEL COACH")
    print("=" * 70)
    print(result["plan"])
