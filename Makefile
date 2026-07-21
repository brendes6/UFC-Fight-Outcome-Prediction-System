# Local Postgres/Redis stack + database migrations.
#
# Usage:
#   make db-up             # start Postgres + Redis (docker compose)
#   make db-migrate        # apply goose migrations in db/migrations
#   make db-reset          # tear down volumes, recreate the stack, and re-run migrations
#   make db-down           # stop the stack (keeps the volume)

DATABASE_URL ?= postgres://ufc:ufc@localhost:5432/ufc?sslmode=disable

# Load testing (k6 against the local stack). ONNXRUNTIME_LIB_PATH points at a
# local ONNX Runtime shared library for the native backend run (macOS: a
# libonnxruntime.dylib); the container/prod image uses its bundled onnxruntime.so.
ONNXRUNTIME_LIB_PATH ?= onnxruntime.so
LOADTEST_BASE_URL ?= http://localhost:8080

.PHONY: db-up db-down db-migrate db-reset loadtest-fixtures loadtest-serve loadtest-cache loadtest-uncached

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

# Regenerate the fighter-tag fixtures the k6 script builds matchups from.
loadtest-fixtures:
	docker exec ufc-postgres psql -U ufc -d ufc -tAc \
	  "SELECT fighter_tag FROM fighters WHERE fighter_tag <> '' ORDER BY \"Elo\" DESC NULLS LAST LIMIT 1000;" \
	  | python3 -c "import sys,json; open('loadtest/fighters.json','w').write(json.dumps([l.strip() for l in sys.stdin if l.strip()]))"
	@echo "Wrote loadtest/fighters.json"

# Run the backend natively against the local stack. Models download from GCS
# (needs ADC) into loadtest/.run. Override ONNXRUNTIME_LIB_PATH on macOS.
loadtest-serve:
	mkdir -p loadtest/.run
	cd loadtest/.run && ONNXRUNTIME_LIB_PATH="$(ONNXRUNTIME_LIB_PATH)" \
	  DATABASE_URL="$(DATABASE_URL)" REDIS_URL="localhost:6379" PORT="8080" \
	  go run ../../backend

loadtest-cache:
	cd loadtest && SCENARIO=cache_hit BASE_URL="$(LOADTEST_BASE_URL)" k6 run predict.js

loadtest-uncached:
	docker exec ufc-redis redis-cli FLUSHDB
	cd loadtest && SCENARIO=uncached BASE_URL="$(LOADTEST_BASE_URL)" k6 run predict.js
