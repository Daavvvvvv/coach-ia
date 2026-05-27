# Coach IA — Sistema multiagente de asistencia táctica para fútbol

**Curso:** Introducción a la Inteligencia Artificial — EAFIT
**Fase:** 1 — Anteproyecto
**Fecha:** Mayo 2026

**Integrantes:**
- David Elias Franco
- Miguel Angel Montoya
- Daniel Sidney Curelop

---

## 1. Problem & Idea

### Problema
El proceso de preparación táctica previo a un partido de fútbol exige procesar un volumen creciente de datos sobre el rival (estadísticas agregadas, formaciones recientes, jugadores clave, debilidades por zona) y cruzarlos con el estado de la propia plantilla para producir un plan de juego coherente: alineación titular, formación e instrucciones tácticas. Este trabajo lo realizan equipos de analistas tácticos de forma manual, es lento y depende del expertise individual.

### Idea
Construir un **sistema multi-agente** basado en LLMs que automatice la fase preparatoria del análisis táctico. Dado el nombre del rival y la plantilla disponible, el sistema produce:

1. Un **scouting** estructurado del rival (fortalezas, debilidades y patrones tácticos).
2. Una **alineación** XI titular con formación recomendada.
3. Tres **instrucciones tácticas** concretas para el partido.

### Por qué es interesante
- Integra la totalidad del bloque de IA generativa del curso: LLMs (Lecture 10), prompt engineering y RAG (Lecture 11), agentes y multi-agente con LangGraph (Lecture 12) y evaluación con LLM-as-judge (Lecture 13).
- Tiene **referencias naturales** para evaluar: la alineación real puesta por el DT en el mismo partido y los resultados deportivos posteriores.
- El dominio cuenta con datos públicos abundantes (FBref, Understat, StatsBomb) y una industria real que ya invierte en herramientas de análisis táctico.

### Tipo de tarea
**NLP + sistemas multi-agente.** La salida es texto estructurado (informe táctico). La evaluación combina métricas estructuradas (overlap de alineación contra la real) y métricas cualitativas (LLM-as-judge sobre coherencia y especificidad táctica).

---

## 2. Proposed Approach

Sistema multi-agente con **dos agentes especializados** orquestados con **LangGraph** siguiendo el patrón orchestrator visto en Lecture 12.

### Arquitectura

```
            ┌──────────────┐
   query →  │  Orchestrator│
            └──────┬───────┘
                   │
            ┌──────▼───────┐      tools: get_team_stats(team)
            │  Scout Agent │              get_recent_matches(team)
            └──────┬───────┘
                   │ scouting report
            ┌──────▼───────┐      tools: get_player_stats(team)
            │  Coach Agent │              propose_lineup(formation, players)
            └──────┬───────┘
                   │
                output (lineup + tactics)
```

### Agente 1 — Scout
- **Rol:** analista del rival.
- **Input:** nombre del equipo rival.
- **Tools:** `get_team_stats(team)`, `get_recent_matches(team)`.
- **Output:** resumen estructurado con fortalezas, debilidades y patrones tácticos del rival (formación más usada, zonas vulnerables, top scorers).

### Agente 2 — Coach
- **Rol:** preparador del plan de partido.
- **Input:** scouting del Scout + plantilla disponible.
- **Tools:** `get_player_stats(team)`, `propose_lineup(formation, players)`.
- **Output:** alineación XI con formación + 3 instrucciones tácticas concretas.

### Orquestador (LangGraph)
- Grafo lineal: `START → scout → coach → END`.
- **State** compartido tipo `MessagesState` extendido con campos `scouting_report` y `final_plan`.

### Justificación
- El **patrón orchestrator** es ideal cuando hay subtareas secuenciales con roles claros, como "primero analiza al rival, luego propón el plan" (referencia: `Lecture12/Agents/multiagent/02_llm_orchestrator_pattern.svg`).
- Se usa un **LLM como motor de razonamiento sobre datos estructurados** en lugar de un modelo predictivo clásico porque la salida deseada es texto explicado (tipo informe), no una clasificación o un valor numérico.
- Las **tools actúan como puente** entre el LLM y los datos reales, evitando alucinaciones — el agente debe llamar a la tool para obtener stats, no inventarlas.
- Se elige LangGraph sobre orquestación manual (vista en `part01_from_prompt_to_action.ipynb`) porque facilita el manejo de state, condiciones y trazabilidad para evaluación.

### Stack técnico
- **LangGraph** — orquestación del grafo multi-agente.
- **LLMs a evaluar** — se contemplan dos modelos para comparar capacidad de razonamiento táctico:
  - **Gemini 2.0 Flash** como baseline gratuito (vía Google AI Studio, ya usado en Lecture 10).
  - **Claude Haiku 4.5** como modelo de mayor capacidad de razonamiento, en caso de que el baseline no alcance la calidad requerida en las métricas cualitativas.
- **Datos** — La Liga 2025-26 descargada offline a CSVs vía la librería `soccerdata` (FBref).
- **Evaluación** — suite con LLM-as-judge siguiendo el patrón de `Lecture13/notebooks/workshop_agent_evals.ipynb`.

---

## 3. Data

### Fuentes
- **FBref** ([fbref.com/en/comps/12/La-Liga-Stats](https://fbref.com/en/comps/12/La-Liga-Stats)) — estadísticas oficiales por equipo, jugador y partido de **La Liga 2025-26**. Acceso vía la librería `soccerdata` o `pandas.read_html`.
- **Understat** ([understat.com/league/La_liga](https://understat.com/league/La_liga)) — datos de Expected Goals (xG) por partido y jugador, usados para enriquecer el scouting con métricas avanzadas.

### Contenido

| Tabla | Filas aprox. | Descripción |
|---|---|---|
| `teams.csv` | 20 | Una fila por equipo: PJ, V/E/D, posesión, xG, xGA, formación más usada |
| `players.csv` | ~600 | Una fila por jugador: posición, minutos, goles, asistencias, xG, xA, pases progresivos, recuperaciones |
| `matches.csv` | 380 | Un partido por fila: home, away, resultado, formaciones, alineaciones titulares |

### Variables

- **Features (X)** — usadas como contexto para los agentes:
  - Stats agregadas de equipo y jugador.
  - Formaciones y alineaciones reales recientes.
  - xG/xA ofensivos y defensivos.
- **"Target" (y)** — no hay un target supervisado tradicional. La evaluación se hace contra dos referencias:
  1. **Alineación real** del DT en cada partido (overlap de jugadores y formación).
  2. **Rúbrica de coherencia táctica** evaluada con LLM-as-judge.

### Tamaño aproximado
- **20 equipos × 38 jornadas = 760 muestras** (cada muestra = un partido con todo su contexto).
- Para evaluación se selecciona un subset balanceado de **30 partidos** estratificado por nivel del equipo: 10 top-6, 10 mitad de tabla, 10 zona baja.

---

## 4. Initial Exploration (EDA)

Esta sección se desarrolla en `notebooks/01_eda.ipynb`. A continuación se describen los plots planeados y las observaciones preliminares esperadas.

### Plots planeados

**Plot 1 — Distribución de xG por equipo en La Liga 25-26**
- Tipo: scatter plot xG creado vs. xG concedido por equipo.
- Objetivo: identificar equipos ofensivos (alto xG creado, bajo xG concedido) vs. defensivos vs. desbalanceados.
- Relevancia: contexto que el agente Scout usará para describir el perfil del rival.

**Plot 2 — Heatmap de formaciones más usadas por equipo**
- Eje X: formación (4-3-3, 4-2-3-1, 3-5-2, etc.).
- Eje Y: equipos.
- Valor: porcentaje de partidos jugados con esa formación.
- Relevancia: permite al agente Coach proponer formaciones realistas para cada plantilla, en línea con el estilo histórico del equipo.

### Observaciones preliminares
*(A confirmar con el notebook de EDA)*

- **Distribución desbalanceada de resultados:** se espera ≈55% victorias locales, ≈22% empates, ≈23% victorias visitantes (patrón típico de ligas top-5). Relevante si en algún momento se entrena un clasificador auxiliar.
- **Outliers esperados:** Real Madrid y Barcelona con xG muy por encima de la media de la liga; equipos recién ascendidos en el extremo opuesto.
- **Datos faltantes:** principalmente en equipos recién ascendidos sin histórico en la plataforma; se manejan filtrando o imputando con la media de equipos de perfil similar.

---

## 5. Question & Objective

### Pregunta
> ¿Puede un sistema multi-agente basado en LLMs producir alineaciones y planes tácticos coherentes con las decisiones reales de los entrenadores profesionales, usando únicamente estadísticas públicas del rival y de la plantilla?

### Objetivo
Construir y evaluar un sistema multi-agente que, dados un rival y una plantilla, produzca:

1. Un **scouting** del rival (fortalezas, debilidades, patrones tácticos).
2. Una **alineación XI** con formación recomendada.
3. **Tres instrucciones tácticas** concretas para el partido.

Y medir la calidad de la salida contra:
- **(a)** las decisiones reales de los DTs en los mismos partidos (overlap de alineación, match de formación), y
- **(b)** una rúbrica de coherencia táctica evaluada con LLM-as-judge.

---

## 6. Evaluation

La evaluación combina métricas **estructuradas** (cuantitativas, ground truth observable) y **cualitativas** (LLM-as-judge sobre rúbricas), siguiendo el patrón system-level evaluation visto en Lecture 13.

### Métricas estructuradas

| # | Métrica | Definición | Baseline |
|---|---|---|---|
| 1 | **Lineup overlap** | Intersección entre los 11 jugadores propuestos y los 11 titulares reales del DT, dividida entre 11 | Aleatoria sobre la plantilla: ≈3-4/11 |
| 2 | **Formation match** | ¿Coincide la formación propuesta con la real? Soft match entre familias (4-3-3 ≈ 4-1-2-3) | Random sobre 5 formaciones comunes: ≈20% |

### Métricas cualitativas (LLM-as-judge)

| # | Métrica | Rúbrica (1-5) |
|---|---|---|
| 3 | **Tactical coherence** | ¿El plan táctico es coherente con el scouting? (Ej.: si el rival es débil por banda derecha, ¿el plan explota esa zona?) |
| 4 | **Specificity** | ¿Las instrucciones son concretas o genéricas? ("presionar alto" = genérico; "presionar al lateral derecho cuando recibe de espaldas" = específico) |
| 5 | **Faithfulness** | ¿Las afirmaciones del scouting están respaldadas por las stats provistas o se inventan datos? |

### Evaluation set
- **30 partidos** de La Liga 2025-26 estratificados:
  - 10 partidos del top-6 (Real Madrid, Barcelona, Atlético, etc.)
  - 10 partidos de mitad de tabla
  - 10 partidos de zona baja / lucha por descenso

### Justificación
La combinación de métricas estructuradas + LLM-as-judge es el estándar actual de evaluación de sistemas LLM no triviales (Lecture 13, sección "Model vs System Evaluation"). Las métricas estructuradas dan rigor cuantitativo y son auditables; las cualitativas capturan dimensiones de calidad (coherencia, especificidad, faithfulness) que no se reducen a un overlap numérico.

---

## 7. References

1. **Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., & Cao, Y.** (2023). *ReAct: Synergizing Reasoning and Acting in Language Models*. ICLR 2023. arXiv:2210.03629.
   → Patrón base de los agentes individuales (razonamiento + uso de tools).

2. **Wei, J., Wang, X., Schuurmans, D., Bosma, M., Ichter, B., Xia, F., Chi, E., Le, Q., & Zhou, D.** (2022). *Chain-of-Thought Prompting Elicits Reasoning in Large Language Models*. NeurIPS 2022. arXiv:2201.11903.
   → Fundamento teórico del razonamiento estructurado en los prompts de cada agente.

3. **Liu, Y., Iter, D., Xu, Y., Wang, S., Xu, R., & Zhu, C.** (2023). *G-Eval: NLG Evaluation using GPT-4 with Better Human Alignment*. EMNLP 2023. arXiv:2303.16634.
   → Base metodológica del LLM-as-judge usado en la evaluación cualitativa.

4. **LangGraph documentation** — LangChain AI. [https://langchain-ai.github.io/langgraph/](https://langchain-ai.github.io/langgraph/).
   → Framework usado para la orquestación multi-agente, patrones de state y conditional edges.

5. **StatsBomb Open Data** — StatsBomb. [https://github.com/statsbomb/open-data](https://github.com/statsbomb/open-data).
   → Documentación de event data y modelo de xG; referencia conceptual para definir las features de scouting.

6. **FBref — Football Statistics and History** — Sports Reference LLC. [https://fbref.com](https://fbref.com).
   → Fuente principal de datos estadísticos para La Liga 2025-26.


---

## Apéndice — Declaración de uso de IA

Para la redacción y estructuración de este documento se usó IA generativa como apoyo. La idea del proyecto, las decisiones técnicas y la validación del contenido fueron realizadas por los integrantes del equipo.
