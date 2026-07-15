import { test, afterEach } from 'node:test';
import assert from 'node:assert/strict';

import { getPredictions, getUpcoming, getPrevious } from './client.js';

const realFetch = globalThis.fetch;
const realConsoleError = console.error;

function jsonResponse(body, { ok = true, status = 200 } = {}) {
  return {
    ok,
    status,
    json: async () => body,
  };
}

afterEach(() => {
  globalThis.fetch = realFetch;
  console.error = realConsoleError;
});

test('getPredictions sends normalized fighter tags, preserving suffixes', async () => {
  let capturedBody;
  globalThis.fetch = async (_url, options) => {
    capturedBody = JSON.parse(options.body);
    return jsonResponse({ prediction: 'red', probability: 0.61 });
  };

  const result = await getPredictions(' Charles Johnson Jr. ', 'Jean-Silva');

  assert.deepEqual(capturedBody, {
    red_fighter: 'charles_johnson_jr.',
    blue_fighter: 'jean_silva',
  });
  assert.deepEqual(result, { prediction: 'red', probability: 0.61 });
});

test('getPredictions returns null when the request fails', async () => {
  console.error = () => {};
  globalThis.fetch = async () => jsonResponse({ error: 'not found' }, { ok: false, status: 404 });

  const result = await getPredictions('Fighter A', 'Fighter B');

  assert.equal(result, null);
});

test('getPredictions returns null when fetch throws', async () => {
  console.error = () => {};
  globalThis.fetch = async () => {
    throw new TypeError('network down');
  };

  const result = await getPredictions('Fighter A', 'Fighter B');

  assert.equal(result, null);
});

test('getUpcoming unwraps the fights array', async () => {
  globalThis.fetch = async () => jsonResponse({ fights: [{ id: 1 }, { id: 2 }] });

  const result = await getUpcoming();

  assert.deepEqual(result, [{ id: 1 }, { id: 2 }]);
});

test('getUpcoming returns an empty array on error', async () => {
  console.error = () => {};
  globalThis.fetch = async () => jsonResponse({}, { ok: false, status: 500 });

  const result = await getUpcoming();

  assert.deepEqual(result, []);
});

test('getPrevious returns an empty array when no fights are present', async () => {
  globalThis.fetch = async () => jsonResponse({});

  const result = await getPrevious();

  assert.deepEqual(result, []);
});
