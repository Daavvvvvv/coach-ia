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

Copia `.env.example` a `.env` y rellena tu `GOOGLE_API_KEY` (sácala en https://aistudio.google.com/app/apikey).

```bash
cp .env.example .env
```

## 5. Verificar

```bash
python -c "import langgraph, langchain, soccerdata; print('OK')"
```

Si imprime `OK` el entorno está listo.
