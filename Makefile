# Makefile

# DB MIGRATIONS
migrate:
	alembic revision --autogenerate -m "$(m)"
upgrade:
	alembic upgrade head
downgrade:
	alembic downgrade -1

# DATA SCRIPTS
populate:
	PYTHONPATH=. python scripts/populate_db.py
reset:
	PYTHONPATH=. python scripts/reset_db.py

# BACKEND
run:
	PYTHONPATH=. venv/bin/python -m uvicorn app.main:app --reload --log-level debug --host 0.0.0.0 --port 8000
