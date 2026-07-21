// k6 load test for the UFC prediction backend service (POST /predict)
//
// The /predict endpoint has two distict code paths for making predictions
// based on potentially recurrent requests:
//
// - cache_hit: Requests are stored in Redis for 6 hours and requests
//    already in the cache are served straight from Redis.
// - uncached: predictions that arent current in the cache (stored as red
//    vs blue matchups) invoke a read of the fighters' stats from Postgres
//    database and features are calculated and passed into the ensembled
//    NN and XGBoost models.
//
// This tool can be ran for each of these scenarios using the following:
//   SCENARIO=cache_hit  k6 run loadtest/predict.js
//   SCENARIO=uncached   k6 run loadtest/predict.js
//
// Target with BASE_URL (default http://localhost:8080).

import http from 'k6/http';
import { check } from 'k6';
import { SharedArray } from 'k6/data';
import { scenario } from 'k6/execution';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';
const SCENARIO = __ENV.SCENARIO || 'uncached';

// Real fighter_tags pulled from the fighters table.
const FIGHTERS = new SharedArray('fighters', () => JSON.parse(open('./fighters.json')));

// Size of the pre-warmed working set for the cache-hit scenario.
const WARM_PAIRS = 20;

// Enumerate the n-th unique ordered pair (a, b), a != b, over FIGHTERS.
// There are N*(N-1) such pairs; callers keep n below that to stay unique.
function pairAt(n) {
  const N = FIGHTERS.length;
  const perA = N - 1;
  const idx = n % (N * perA);
  const a = Math.floor(idx / perA);
  let b = idx % perA;
  if (b >= a) b += 1; // skip a == b
  return { red_fighter: FIGHTERS[a], blue_fighter: FIGHTERS[b] };
}

const scenarios = {
  // Steady VUs hammering the warm set for a fixed window -> throughput + tail
  // latency of the Redis-served path.
  cache_hit: {
    executor: 'constant-vus',
    vus: 40,
    duration: '30s',
  },
  // Unique matchups for a fixed window (Redis flushed first) so every request
  // is a genuine cache miss. 999k unique pairs >> requests in the window, so
  // no matchup repeats back into the cache mid-run.
  uncached: {
    executor: 'constant-vus',
    vus: 50,
    duration: '30s',
  },
};

export const options = {
  scenarios: { [SCENARIO]: scenarios[SCENARIO] },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<250', 'p(99)<500'],
  },
};

// Pre-warm the cache-hit working set so the measured window is pure hits.
export function setup() {
  if (SCENARIO !== 'cache_hit') return;
  for (let i = 0; i < WARM_PAIRS; i++) {
    http.post(`${BASE_URL}/predict`, JSON.stringify(pairAt(i)), {
      headers: { 'Content-Type': 'application/json' },
    });
  }
}

export default function () {
  const n = scenario.iterationInTest;
  const body = SCENARIO === 'cache_hit' ? pairAt(n % WARM_PAIRS) : pairAt(n);
  const res = http.post(`${BASE_URL}/predict`, JSON.stringify(body), {
    headers: { 'Content-Type': 'application/json' },
    tags: { path: SCENARIO },
  });
  check(res, {
    'status 200': (r) => r.status === 200,
    'has red_ko': (r) => r.json('red_ko') !== undefined,
  });
}
