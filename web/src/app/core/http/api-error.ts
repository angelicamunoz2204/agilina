/**
 * What the web reads of an error of the API. Every failure answers with the same body,
 * `{ error: { status, code, message, details?, request_id } }`; the web decides by `code`
 * and never shows `message`, which is for developers.
 */
export interface ApiErrorBody {
  readonly code: string;
  readonly reasons: readonly string[];
  readonly requestId?: string | undefined;
}

/** The error in the body of a failed response, or `undefined` if it is not the API's. */
export function readApiError(body: unknown): ApiErrorBody | undefined {
  const error = (body as { error?: unknown } | null | undefined)?.error;
  if (typeof error !== 'object' || error === null) {
    return undefined;
  }
  const {
    code,
    details,
    request_id: requestId,
  } = error as {
    code?: unknown;
    details?: { reasons?: unknown };
    request_id?: unknown;
  };
  if (typeof code !== 'string') {
    return undefined;
  }
  const reasons = details?.reasons;
  return {
    code,
    reasons: Array.isArray(reasons)
      ? reasons.filter((r): r is string => typeof r === 'string')
      : [],
    requestId: typeof requestId === 'string' ? requestId : undefined,
  };
}
