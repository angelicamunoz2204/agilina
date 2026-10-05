import { type Provider } from '@angular/core';

import { Logger, type LogContext } from '@core/logging/logger';

interface RecordedEntry {
  readonly level: 'debug' | 'info' | 'warn' | 'error';
  readonly message: string;
  readonly context?: LogContext;
  readonly error?: unknown;
}

/** Logger double that remembers what was logged, to assert that errors are not swallowed. */
export class FakeLogger extends Logger {
  readonly entries: RecordedEntry[] = [];

  debug(message: string, context?: LogContext): void {
    this.record({ level: 'debug', message, ...(context && { context }) });
  }

  info(message: string, context?: LogContext): void {
    this.record({ level: 'info', message, ...(context && { context }) });
  }

  warn(message: string, context?: LogContext): void {
    this.record({ level: 'warn', message, ...(context && { context }) });
  }

  error(message: string, error?: unknown, context?: LogContext): void {
    this.record({
      level: 'error',
      message,
      ...(error === undefined ? {} : { error }),
      ...(context && { context }),
    });
  }

  private record(entry: RecordedEntry): void {
    this.entries.push(entry);
  }
}

export function provideFakeLogger(): Provider {
  return { provide: Logger, useClass: FakeLogger };
}
