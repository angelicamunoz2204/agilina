import { parseRuntimeConfig, RuntimeConfigError, type RuntimeConfig } from './runtime-config';

/** Relative to <base href>, so the app can live under any path. */
const RUNTIME_CONFIG_PATH = 'config.json';

/** Fetches and validates config.json. It runs before Angular bootstraps. */
export async function loadRuntimeConfig(fetchFn: typeof fetch = fetch): Promise<RuntimeConfig> {
  const response = await fetchFn(RUNTIME_CONFIG_PATH, { cache: 'no-store' });
  if (!response.ok) {
    throw new RuntimeConfigError(`Could not load ${RUNTIME_CONFIG_PATH}: HTTP ${response.status}`);
  }
  return parseRuntimeConfig(await response.json());
}
