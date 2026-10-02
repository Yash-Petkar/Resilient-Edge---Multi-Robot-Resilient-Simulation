/**
 * Normalizes the Vite demo-mode flag. Keeping this pure makes the mode switch
 * independently testable while ApiService remains the authoritative consumer.
 */
export function resolveDemoMode(value: unknown): boolean {
  return String(value ?? '').trim().toLowerCase() === 'true';
}
