# Load testing

Load tests for the Go inference service (POST /predict) using [k6](https://k6.io/).

/predict has two very different code paths, and the whole point of the test is
to measure them separately, reporting a single blended latency number would
be meaningless:

- **cache-hit** — a small, pre-warmed set of matchups is replayed, so every
  request is served straight from Redis. Isolates the hot path.
- **uncached** — a large pool of unique matchups (Redis flushed first) so every
  request misses the cache and exercises the full pipeline: two concurrent
  Postgres reads → feature engineering → concurrent ONNX ensemble inference
  (NN softmax + XGBoost), averaged.

## Results

Measured against the local stack (backend + Postgres + Redis all on one machine,
no network hop), 40–50 virtual users, k6 v2.1.0.

| Path | Throughput | p50 | p95 | p99 | Errors |
|------|-----------:|----:|----:|----:|-------:|
| Cache-hit (Redis)                       | ~19,000 req/s | 1.5 ms | 3.5 ms | 6.7 ms | 0% |
| Uncached (Postgres + ONNX ensemble)     | ~4,900 req/s  | 9.6 ms | 14 ms  | 18 ms  | 0% |

Representative warm-process run (583k requests cache-hit, 148k uncached); there is
some run-to-run variance, especially on the uncached tail (p99 has been seen up to
~45 ms under competing load).

## Prerequisites

- Local stack running: `make db-up` (Postgres + Redis) with the 'fighters' table
  populated.
- [k6](https://grafana.com/docs/k6/latest/set-up/install-k6/) installed
  (`brew install k6`).
- A local ONNX Runtime shared library for the native backend run. On macOS this
  is a `libonnxruntime.dylib` (e.g. from `pip install onnxruntime`); point
  `ONNXRUNTIME_LIB_PATH` at it. In the container/prod image the bundled
  `onnxruntime.so` is used automatically.
- Application Default Credentials for GCS (`gcloud auth application-default
  login`) so the backend can pull the production models at startup.

## Running

```bash
# 1. (once) regenerate the fighter-tag fixtures from the local DB
make loadtest-fixtures

# 2. start the backend natively against the local stack (separate terminal)
make loadtest-serve ONNXRUNTIME_LIB_PATH=/path/to/libonnxruntime.dylib

# 3. run each scenario
make loadtest-cache       # cache-hit path
make loadtest-uncached    # flushes Redis, then the full-inference path
```

loadtest-uncached flushes the Redis DB first so every matchup is a genuine
miss; the fixture pool (1,000 fighters → ~999k unique matchups) is far larger
than the requests issued in the window, so no matchup repeats back into the
cache mid-run.

