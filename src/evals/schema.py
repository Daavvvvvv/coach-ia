"""Schemas Pydantic para la eval suite."""
from pydantic import BaseModel, Field


class CoachPlan(BaseModel):
    """Plan táctico estructurado producido por el Coach (o extraído de su markdown)."""

    xi: list[str] = Field(
        description="11 nombres de jugadores que componen el XI titular propuesto.",
        min_length=11,
        max_length=11,
    )
    formation: str = Field(
        description="Formación tipo 'X-Y-Z' (ej. '4-3-3', '4-4-2', '3-5-2').",
    )
    instructions: list[str] = Field(
        description="Exactamente 3 instrucciones tácticas concretas y accionables.",
        min_length=3,
        max_length=3,
    )


class JudgeScore(BaseModel):
    """Puntuación del juez para una dimensión cualitativa."""

    score: int = Field(
        description="Puntaje entero de 0 a 5 (0=muy mal, 5=excelente).",
        ge=0,
        le=5,
    )
    rationale: str = Field(
        description="Una o dos frases explicando el puntaje.",
    )


class JudgeResult(BaseModel):
    """Las 3 dimensiones que evalúa el juez sobre el plan del Coach."""

    tactical_coherence: JudgeScore = Field(
        description="¿El plan es internamente coherente? ¿XI, formación e instrucciones encajan entre sí y con el análisis del rival?",
    )
    specificity: JudgeScore = Field(
        description="¿Las instrucciones son específicas y accionables, o genéricas y vacías?",
    )
    faithfulness: JudgeScore = Field(
        description="¿Las afirmaciones del plan están respaldadas por los datos disponibles? ¿O inventa números/eventos?",
    )
