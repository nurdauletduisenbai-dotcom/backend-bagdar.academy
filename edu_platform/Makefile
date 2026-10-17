.PHONY: up down migrate test lint seed

up:
	docker compose up -d --build

down:
	docker compose down

migrate:
	python manage.py makemigrations accounts organizations courses content videos questions assessments assignments schedule progress notifications payments audit common
	python manage.py migrate

test:
	pytest --ds=config.settings.dev -v

lint:
	ruff check .
	mypy .

seed:
	python seed_data.py
