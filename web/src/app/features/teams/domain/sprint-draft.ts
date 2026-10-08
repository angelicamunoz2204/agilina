/**
 * The whole configuration of a sprint, as it is sent to create it or to edit the active one.
 * The daily's time is an instant in UTC (its wall-clock time on the start date, in the browser
 * of whoever saves) and travels with that browser's IANA time zone (AD-31).
 */
export interface SprintDraft {
  /** `YYYY-MM-DD`. */
  readonly startDate: string;
  /** `YYYY-MM-DD`, included. */
  readonly endDate: string;
  /** ISO 8601 instant in UTC. */
  readonly dailyTime: string;
  readonly timeZone: string;
  /** The `userId` of the participants, in turn order. */
  readonly participants: readonly string[];
}

/** The sprint form as the person fills it: dates, the daily's wall-clock time and the order. */
export interface SprintFields {
  /** `YYYY-MM-DD`, or empty while not chosen. */
  readonly startDate: string;
  /** `YYYY-MM-DD`, or empty while not chosen. */
  readonly endDate: string;
  /** `HH:MM` in the browser's time zone, or empty while not chosen. */
  readonly dailyTime: string;
  readonly participants: readonly string[];
}

/** Why the end date cannot be saved. */
export type EndDateProblem = 'blank' | 'before_start';

/** Why the daily's participants cannot be saved. */
export type ParticipantsProblem = 'none' | 'duplicate';

/** What is wrong with each part of the sprint form; null when that part is fine. */
export interface SprintFieldsProblems {
  readonly startDate: 'blank' | null;
  readonly endDate: EndDateProblem | null;
  readonly dailyTime: 'blank' | null;
  readonly participants: ParticipantsProblem | null;
}

/**
 * The rules of the sprint form: both dates and the daily's time chosen, an end that is not
 * before the start (the same day is fine; every calendar day counts, weekends too) and at
 * least one participant, none twice. Dates in `YYYY-MM-DD` compare as text. This is a
 * convenience for the user: the API applies the same rules and has the last word.
 */
export function sprintFieldsProblems(fields: SprintFields): SprintFieldsProblems {
  return {
    startDate: fields.startDate === '' ? 'blank' : null,
    endDate: endDateProblem(fields.startDate, fields.endDate),
    dailyTime: fields.dailyTime === '' ? 'blank' : null,
    participants: participantsProblem(fields.participants),
  };
}

/** Whether the sprint form can be saved: no part has a problem. */
export function areSprintFieldsValid(problems: SprintFieldsProblems): boolean {
  return (
    problems.startDate === null &&
    problems.endDate === null &&
    problems.dailyTime === null &&
    problems.participants === null
  );
}

function endDateProblem(startDate: string, endDate: string): EndDateProblem | null {
  if (endDate === '') {
    return 'blank';
  }
  return startDate !== '' && endDate < startDate ? 'before_start' : null;
}

function participantsProblem(participants: readonly string[]): ParticipantsProblem | null {
  if (participants.length === 0) {
    return 'none';
  }
  return new Set(participants).size === participants.length ? null : 'duplicate';
}
