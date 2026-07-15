import { test } from 'node:test';
import assert from 'node:assert/strict';

import { normalizeFighterTag } from './fighters.js';

test('lowercases and joins words with underscores', () => {
  assert.equal(normalizeFighterTag('Max Holloway'), 'max_holloway');
});

test('collapses irregular internal whitespace', () => {
  assert.equal(normalizeFighterTag('Max   Holloway'), 'max_holloway');
});

test('trims leading and trailing whitespace', () => {
  assert.equal(normalizeFighterTag('  Islam Makhachev  '), 'islam_makhachev');
});

test('treats hyphens as word separators', () => {
  assert.equal(normalizeFighterTag('Jean-Silva'), 'jean_silva');
});

test('preserves Jr/Sr suffixes to match the stored fighter_tag', () => {
  // The pipeline does NOT strip suffixes, so neither can the client.
  assert.equal(normalizeFighterTag('Charles Johnson Jr.'), 'charles_johnson_jr.');
  assert.equal(normalizeFighterTag('Marvin Vettori Sr'), 'marvin_vettori_sr');
});

test('returns an empty string for blank or non-string input', () => {
  assert.equal(normalizeFighterTag('   '), '');
  assert.equal(normalizeFighterTag(''), '');
  assert.equal(normalizeFighterTag(null), '');
  assert.equal(normalizeFighterTag(undefined), '');
});
