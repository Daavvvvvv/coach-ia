"""LLM-as-judge sobre el plan del Coach. Modelo: Claude Sonnet 4.6 (más capaz que el agente)."""
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic

from src.evals.schema import CoachPlan, JudgeResult

load_dotenv()

_llm = ChatAnthropic(model="claude-sonnet-4-6", temperature=0)
_judge = _llm.with_structured_output(JudgeResult)

_PROMPT_TEMPLATE = """Eres un evaluador experto de planes tácticos de fútbol. Tu tarea es puntuar de 0 a 5 el plan que un agente Coach produjo para un partido de La Liga 2025-26.

Tienes tres entradas:
1. El SCOUTING del rival (producido por otro agente, ya validado).
2. El PLAN del Coach (XI + formación + 3 instrucciones tácticas).
3. Contexto del partido: {our_team} (nuestro equipo) vs {opponent} (rival).

Evalúa estas tres dimensiones, cada una con score 0-5 y una o dos frases de justificación:

- **tactical_coherence**: ¿el XI, la formación y las instrucciones son internamente consistentes y responden al perfil del rival descrito en el scouting? 5 = totalmente coherente; 0 = contradictorio o desconectado.
- **specificity**: ¿las 3 instrucciones son concretas, accionables y específicas a este partido, o son generalidades ("jugar bien", "estar concentrados") que aplicarían a cualquier partido? 5 = muy específicas; 0 = puro lugar común.
- **faithfulness**: ¿las afirmaciones del plan están respaldadas por datos del scouting o son inventadas? Si el plan cita PPDA, xG, jugadores concretos, valora si esos datos son consistentes con el scouting. 5 = todo respaldado; 0 = mucho inventado.

Sé estricto. No infles puntuaciones. Un plan competente promedia 3-4; un plan excelente requiere argumentos fuertes para llegar a 5.

---

# SCOUTING DEL RIVAL ({opponent})

{scouting}

---

# PLAN DEL COACH ({our_team})

**Formación:** {formation}

**XI titular:**
{xi_block}

**Instrucciones tácticas:**
{instructions_block}

---

Ahora puntúa las tres dimensiones."""


def judge_plan(
    plan: CoachPlan, scouting: str, our_team: str, opponent: str
) -> JudgeResult:
    xi_block = "\n".join(f"  {i + 1}. {p}" for i, p in enumerate(plan.xi))
    instructions_block = "\n".join(f"  {i + 1}. {ins}" for i, ins in enumerate(plan.instructions))
    prompt = _PROMPT_TEMPLATE.format(
        our_team=our_team,
        opponent=opponent,
        scouting=scouting,
        formation=plan.formation,
        xi_block=xi_block,
        instructions_block=instructions_block,
    )
    return _judge.invoke(prompt)
