/**
 * Fighter-tag normalization.
 *
 * The backend looks fighters up in PostgreSQL by a normalized primary key
 * ("fighter_tag"). That ID is produced by the data pipeline in
 * `fight-scraper/data_cleaning.py` as:
 *
 *     "_".join(name.lower().replace("-", " ").split())
 *
 * The frontend must build the exact same tag or the lookup misses. In
 * particular, suffixes such as "Jr"/"Sr" are NOT stripped — they are part of
 * the stored document ID, so stripping them here would break predictions for
 * those fighters.
 *
 * @param {string} name Human-entered fighter name.
 * @returns {string} Normalized fighter tag (empty string for blank input).
 */
export function normalizeFighterTag(name) {
  if (typeof name !== 'string') {
    return '';
  }

  return name
    .trim()
    .toLowerCase()
    .replaceAll('-', ' ')
    .split(/\s+/)
    .filter(Boolean)
    .join('_');
}
