# DocSuite Backend

Backend FastAPI para DocAnalyzer y DocActa.

## Stack

- Python 3.11+
- FastAPI
- PostgreSQL 16
- SQLAlchemy 2
- Alembic
- JWT
- OpenAI GPT-4o
- Whisper large-v3
- pyannote speaker diarization community-1

## Inicio local

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

## Docker

```bash
cd docker
docker compose up --build
```

## Base de datos

```bash
python scripts/create_db.py
python scripts/seed_db.py
```

DataGrip puede conectarse a:

```text
Host: localhost
Port: 5432
Database: docsuite
User: postgres
Password: postgres
```
