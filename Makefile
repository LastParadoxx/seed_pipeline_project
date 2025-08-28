.PHONY: setup db migrate ingest api test lint fmt

VENV?=.venv
PYTHON?=${VENV}/bin/python
PIP?=${VENV}/bin/pip
UVI?=${VENV}/bin/uvicorn

setup:
	python3 -m venv ${VENV}
	${PIP} install --upgrade pip
	${PIP} install -e .[test]

# Start the postgres database via docker
db:
	docker-compose up -d db

# Run migrations (uses alembic if present)
migrate:
	${PYTHON} -c "print('No migrations yet – you can integrate Alembic later.')"

# Ingest a folder of JSON files
ingest:
	${PYTHON} -m seed_pipeline.ingest.cli $(ARGS)

# Run the API locally with uvicorn
api:
	${UVI} seed_pipeline.api.main:app --reload --port 8000

test:
	${VENV}/bin/pytest -q

lint:
	${VENV}/bin/flake8 src

fmt:
	${VENV}/bin/black src
