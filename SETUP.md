# Setup local

Pasos para clonar y dejar el repo corriendo en tu máquina.

## 1. Clonar

```bash
git clone https://github.com/Daavvvvvv/coach-ia.git
cd coach-ia
```

## 2. Crear y activar el venv

```bash
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows
```

## 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

## 4. Variables de entorno

Copia `.env.example` a `.env` y rellena tu `ANTHROPIC_API_KEY` (sácala en https://console.anthropic.com/settings/keys).

```bash
cp .env.example .env
```

## 5. Verificar

```bash
python -c "import langgraph, langchain, langchain_anthropic, soccerdata; print('OK')"
```

Si imprime `OK` el entorno está listo.

## 6. Correr el sistema

Los datos ya vienen descargados en `data/processed/`, así que no hace falta bajar nada. Los comandos para correr los agentes, el sistema completo y la evaluación están en el [README](README.md#cómo-correr).

> Correr los agentes y la eval necesita la `ANTHROPIC_API_KEY`. Si no tienes una, los resultados de la última corrida ya están en `evals/results/` y los notebooks los leen sin re-ejecutar.
