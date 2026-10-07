import { InjectionToken } from '@angular/core';

import { LOG_LEVELS, type LogLevel } from '../logging/log-level';

/**
 * Settings that change per environment. They are read from environment
 * variables when the container starts (runtime-config.template.json) and loaded
 * before bootstrap, so no URL or identifier is compiled into the bundle.
 * It never holds secrets: everything here is public by nature.
 */
export interface RuntimeConfig {
  /** Base URL of the API, without a trailing slash. */
  readonly apiUrl: string;
  readonly keycloak: {
    readonly url: string;
    /** A tenant's realm is this prefix and its name: `agilina-` and `acme` give `agilina-acme`. */
    readonly realmPrefix: string;
    readonly clientId: string;
  };
  /** Minimum level the logger writes. */
  readonly logLevel: LogLevel;
}

export const RUNTIME_CONFIG = new InjectionToken<RuntimeConfig>('RUNTIME_CONFIG');

export class RuntimeConfigError extends Error {
  override readonly name = 'RuntimeConfigError';
}

/**
 * Validates the raw content of config.json. It throws with every problem at once
 * so that a misconfigured deployment is fixed in one go.
 */
export function parseRuntimeConfig(raw: unknown): RuntimeConfig {
  const problems: string[] = [];
  const source = asRecord(raw);
  const keycloak = asRecord(source['keycloak']);

  const apiUrl = requiredText(source['apiUrl'], 'apiUrl', problems);
  const keycloakUrl = requiredText(keycloak['url'], 'keycloak.url', problems);
  const realmPrefix = requiredText(keycloak['realmPrefix'], 'keycloak.realmPrefix', problems);
  const clientId = requiredText(keycloak['clientId'], 'keycloak.clientId', problems);
  const logLevel = parseLogLevel(source['logLevel'], problems);

  if (problems.length > 0) {
    throw new RuntimeConfigError(`Invalid runtime config: ${problems.join('; ')}`);
  }
  return {
    apiUrl: withoutTrailingSlash(apiUrl),
    keycloak: { url: withoutTrailingSlash(keycloakUrl), realmPrefix, clientId },
    logLevel,
  };
}

function asRecord(value: unknown): Record<string, unknown> {
  return typeof value === 'object' && value !== null ? (value as Record<string, unknown>) : {};
}

function requiredText(value: unknown, field: string, problems: string[]): string {
  if (typeof value !== 'string' || value.trim() === '') {
    problems.push(`${field} is missing`);
    return '';
  }
  // envsubst leaves the placeholder untouched when the variable is not defined.
  if (value.includes('${')) {
    problems.push(`${field} was not rendered (${value})`);
    return '';
  }
  return value.trim();
}

/** Accepts the levels of AGILINA_LOG_LEVEL (DEBUG, INFO, WARNING, ERROR) in any case. */
function parseLogLevel(value: unknown, problems: string[]): LogLevel {
  const text = typeof value === 'string' ? value.trim().toLowerCase() : '';
  const level = text === 'warning' ? 'warn' : text;
  const known = LOG_LEVELS.find((candidate) => candidate === level);
  if (known === undefined) {
    problems.push(`logLevel must be one of ${LOG_LEVELS.join(', ')}`);
    return 'info';
  }
  return known;
}

function withoutTrailingSlash(url: string): string {
  return url.replace(/\/+$/, '');
}
