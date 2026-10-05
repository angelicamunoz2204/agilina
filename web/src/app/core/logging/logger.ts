/**
 * Structured data attached to a log entry. Keys in camelCase. Never put tokens,
 * passwords, full email addresses or audio content here.
 */
export type LogContext = Readonly<Record<string, unknown>>;

/**
 * Port for the application log. Every error that is handled is also logged
 * through here; nothing writes to the console directly (ESLint `no-console`).
 *
 * Messages are for developers: English, short and stable, so that they can be
 * searched. What the user reads goes through i18n, never through the logger.
 */
export abstract class Logger {
  abstract debug(message: string, context?: LogContext): void;
  abstract info(message: string, context?: LogContext): void;
  abstract warn(message: string, context?: LogContext): void;
  abstract error(message: string, error?: unknown, context?: LogContext): void;
}
