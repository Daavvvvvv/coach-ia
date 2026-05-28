"""Extrae un CoachPlan estructurado a partir del markdown libre que devuelve el Coach."""
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic

from src.evals.schema import CoachPlan

load_dotenv()

_llm = ChatAnthropic(model="claude-haiku-4-5-20251001", temperature=0)
_extractor = _llm.with_structured_output(CoachPlan)

_PROMPT = """Lee el siguiente plan táctico escrito en markdown y extrae:
- xi: los 11 nombres de los jugadores del XI titular, en el orden en que aparecen.
- formation: la formación (formato 'X-Y-Z' como '4-3-3', '4-4-2').
- instructions: las 3 instrucciones tácticas, cada una como una sola cadena de texto autocontenida.

Sé fiel al texto. No reformules ni inventes.

---
"""


def extract_plan(markdown: str) -> CoachPlan:
    return _extractor.invoke(_PROMPT + markdown)
