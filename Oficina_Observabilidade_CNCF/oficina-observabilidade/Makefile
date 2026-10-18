.PHONY: up down logs test ps
up:
	docker compose up -d --build
down:
	docker compose down
logs:
	docker compose logs -f --tail=100
ps:
	docker compose ps
test:
	python -m unittest discover -s tests -v
