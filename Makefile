.PHONY: install lint typecheck test eval index run docker-build

install:
	cd backend && pip install -r requirements-dev.txt

lint:
	cd backend && ruff check .
	cd backend && ruff format --check .

typecheck:
	cd backend && mypy app tests

test:
	cd backend && pytest

eval:
	cd backend && python eval/run.py

index:
	cd backend && python scripts/build_index.py

run:
	cd backend && uvicorn app.main:create_app --factory --reload --port 8000

docker-build:
	docker build -t aira-backend -f backend/Dockerfile .
