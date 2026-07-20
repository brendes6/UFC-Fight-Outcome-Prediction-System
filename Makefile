# Local Postgres/Redis stack + database migrations.
#
# Usage:
#   make db-up             # start Postgres + Redis (docker compose)
#   make db-migrate        # apply goose migrations in db/migrations
#   make db-reset          # tear down volumes, recreate the stack, and re-run migrations
#   make db-down           # stop the stack (keeps the volume)

DATABASE_URL ?= postgres://ufc:ufc@localhost:5432/ufc?sslmode=disable

.PHONY: db-up db-down db-migrate db-reset

db-up:
	docker compose up -d

db-down:
	docker compose down

db-migrate:
	go run github.com/pressly/goose/v3/cmd/goose@latest -dir db/migrations postgres "$(DATABASE_URL)" up

db-reset:
	docker compose down -v
	docker compose up -d
	@echo "Waiting for Postgres to be healthy..."
	@until docker exec ufc-postgres pg_isready -U ufc -d ufc >/dev/null 2>&1; do sleep 1; done
	$(MAKE) db-migrate
	@echo "Schema ready (empty). The scraper and odds jobs populate the tables."
