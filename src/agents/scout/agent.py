"""Agente Scout — perfila un rival de La Liga 25-26 con tools sobre los CSVs."""
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent

from src.agents.scout.tools import get_recent_matches, get_team_profile

load_dotenv()

SCOUT_PROMPT = """Eres un scout de fútbol experto, especializado en La Liga española temporada 2025-26.

Tu tarea: dado un equipo rival, producir un scouting estructurado para preparar el partido. Usa SIEMPRE las herramientas para obtener datos reales; no inventes cifras.

Sigue esta estructura:

1. **Resumen** — equipo, partidos jugados, puntos reales y esperados (xpuntos). Si los puntos están muy por encima de xpuntos, el equipo ha sobrerendido; si están por debajo, ha tenido mala suerte o ha sido ineficaz.
2. **Estilo de juego** — describe presion (alta/media/baja) y ataque (dominante/medio/limitado) apoyándote en los números crudos (PPDA, deep_completions_total).
3. **Fortalezas y debilidades** — contrasta xg_favor con xg_contra para identificar perfil ofensivo/defensivo.
4. **Estado de forma** — usa get_recent_matches y comenta los últimos 5 partidos (rachas, marcadores claros vs ajustados, si los xG van con los resultados o no).
5. **Cómo enfrentarlo** — 2-3 ideas concretas para un entrenador rival.

Sé conciso, técnico, en español. No uses bullets vacíos; si no tienes datos para una sección, dilo."""


def build_scout_agent():
    llm = ChatAnthropic(model="claude-haiku-4-5-20251001", temperature=0.2)
    return create_react_agent(
        model=llm,
        tools=[get_team_profile, get_recent_matches],
        prompt=SCOUT_PROMPT,
    )


if __name__ == "__main__":
    agent = build_scout_agent()
    rival = "Villarreal"
    print(f"=== Scouting: {rival} ===\n")
    result = agent.invoke(
        {"messages": [{"role": "user", "content": f"Hazme el scouting del {rival}."}]}
    )
    print(result["messages"][-1].content)
