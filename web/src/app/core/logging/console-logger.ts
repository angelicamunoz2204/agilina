import { Injectable, inject } from '@angular/core';

import { isLevelEnabled, type LogLevel } from './log-level';
import { Logger, type LogContext } from './logger';
import { RUNTIME_CONFIG } from '../config/runtime-config';

/** One line of the log, the same shape whatever adapter writes it. */
export interface LogEntry {
  readonly level: LogLevel;
  readonly message: string;
  /** ISO 8601 in UTC. */
  readonly timestamp: string;
  readonly context?: LogContext;
  readonly error?: unknown;
}

/**
 * Adapter of the Logger port that writes structured entries to the browser
 * console. Sending them elsewhere (the API, an error tracker) is a new adapter
 * bound in app.config.ts; callers do not change.
 */
@Injectable()
export class ConsoleLogger extends Logger {
  private readonly threshold = inject(RUNTIME_CONFIG).logLevel;

  debug(message: string, context?: LogContext): void {
    this.write('debug', message, context);
  }

  info(message: string, context?: LogContext): void {
    this.write('info', message, context);
  }

  warn(message: string, context?: LogContext): void {
    this.write('warn', message, context);
  }

  error(message: string, error?: unknown, context?: LogContext): void {
    this.write('error', message, context, error);
  }

  private write(level: LogLevel, message: string, context?: LogContext, error?: unknown): void {
    if (!isLevelEnabled(level, this.threshold)) {
      return;
    }
    const entry: LogEntry = {
      level,
      message,
      timestamp: new Date().toISOString(),
      ...(context === undefined ? {} : { context }),
      ...(error === undefined ? {} : { error }),
    };
    console[level](`[${level}] ${message}`, entry);
  }
}
