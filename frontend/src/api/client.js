import { normalizeFighterTag } from '../domain/fighters.js';

// The deployed Cloud Run backend. Overridable at build time with VITE_API_URL
// so the app can point at a local backend during development.
const DEFAULT_API_URL = 'https://ufc-predictions-685306641609.us-central1.run.app';

const API_URL = (import.meta.env?.VITE_API_URL || DEFAULT_API_URL).replace(/\/+$/, '');

async function requestJson(path, options) {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: { Accept: 'application/json', ...options?.headers },
  });

  const payload = await response.json().catch(() => null);

  if (!response.ok) {
    const message = payload?.error || `Request failed with HTTP ${response.status}`;
    throw new Error(message);
  }

  return payload;
}

export async function getRoot() {
  try {
    return await requestJson('/');
  } catch (error) {
    console.error('Error fetching service status:', error);
    return null;
  }
}

export async function getPredictions(redFighter, blueFighter) {
  try {
    return await requestJson('/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        red_fighter: normalizeFighterTag(redFighter),
        blue_fighter: normalizeFighterTag(blueFighter),
      }),
    });
  } catch (error) {
    console.error('Error fetching prediction:', error);
    return null;
  }
}

export async function getUpcoming() {
  try {
    const payload = await requestJson('/upcoming');
    return payload?.fights || [];
  } catch (error) {
    console.error('Error fetching upcoming fights:', error);
    return [];
  }
}

export async function getPrevious() {
  try {
    const payload = await requestJson('/previous');
    return payload?.fights || [];
  } catch (error) {
    console.error('Error fetching previous fights:', error);
    return [];
  }
}
