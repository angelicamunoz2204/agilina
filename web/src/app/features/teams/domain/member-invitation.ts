/** Longest name the API accepts for an invited person. */
export const FULL_NAME_MAX_LENGTH = 200;

/** Longest email address the API accepts (RFC 5321). */
export const EMAIL_MAX_LENGTH = 254;

/** Why the name of an invited person cannot be sent. */
export type FullNameProblem = 'blank' | 'too_long';

/** Why the email of an invited person cannot be sent. */
export type EmailProblem = 'blank' | 'invalid' | 'too_long';

/** What is wrong with each field of an invitation; null when the field is fine. */
export interface InvitationProblems {
  readonly fullName: FullNameProblem | null;
  readonly email: EmailProblem | null;
}

/** Something, an @, something, a dot and something, without spaces: the API's own pattern. */
const EMAIL = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

/**
 * The rule of the invitation form: a name that is not blank and an email the API would take,
 * both trimmed. Characters are counted as code points (`Array.from`), the way the API counts
 * them. This is a convenience for the user: the API applies the same rule and has the last
 * word.
 */
export function invitationProblems(fullName: string, email: string): InvitationProblems {
  return { fullName: fullNameProblem(fullName), email: emailProblem(email) };
}

/** Whether an invitation can be sent: no field has a problem. */
export function isInvitationValid(problems: InvitationProblems): boolean {
  return problems.fullName === null && problems.email === null;
}

function fullNameProblem(raw: string): FullNameProblem | null {
  const name = raw.trim();
  if (name === '') {
    return 'blank';
  }
  return Array.from(name).length > FULL_NAME_MAX_LENGTH ? 'too_long' : null;
}

function emailProblem(raw: string): EmailProblem | null {
  const email = raw.trim();
  if (email === '') {
    return 'blank';
  }
  if (Array.from(email).length > EMAIL_MAX_LENGTH) {
    return 'too_long';
  }
  return EMAIL.test(email) ? null : 'invalid';
}
