/**
 * Shared formatting utilities for the Eldritch Archive frontend.
 */

/**
 * Format a raw entity ID into a display name.
 * Strips known prefixes (CHARACTER., CARD., RELIC., ENCOUNTER., etc.)
 * and converts UPPER_SNAKE_CASE to Title Case.
 *
 * Examples:
 *   CHARACTER.IRONCLAD       -> Ironclad
 *   CARD.POMMEL_STRIKE       -> Pommel Strike
 *   RELIC.DEAD_BRANCH        -> Dead Branch
 *   ENCOUNTER.THE_CORRUPTOR  -> The Corruptor
 */
export function fmt(id) {
  return id
    .replace(/^[A-Z_]+\./, '')
    .replace(/_/g, ' ')
    .toLowerCase()
    .replace(/\b\w/g, c => c.toUpperCase());
}

export function pct(v) {
  return (v * 100).toFixed(1) + '%';
}

export function fmtTime(s) {
  if (!s) return '—';
  const m = Math.floor(s / 60), sec = Math.floor(s % 60);
  return m > 60 ? `${Math.floor(m / 60)}h ${m % 60}m` : `${m}:${String(sec).padStart(2, '0')}`;
}

export function wrColor(rate) {
  if (rate >= 0.55) return 'var(--secondary)';
  if (rate >= 0.40) return 'var(--primary)';
  return 'var(--tertiary-dim)';
}
