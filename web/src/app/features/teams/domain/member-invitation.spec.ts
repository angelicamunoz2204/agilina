import {
  EMAIL_MAX_LENGTH,
  FULL_NAME_MAX_LENGTH,
  invitationProblems,
  isInvitationValid,
} from './member-invitation';

describe('invitationProblems', () => {
  it('accepts a name and an email the API would take', () => {
    const problems = invitationProblems('Julián Torres', 'julian@example.com');

    expect(problems).toEqual({ fullName: null, email: null });
    expect(isInvitationValid(problems)).toBeTrue();
  });

  it('trims both fields before judging them', () => {
    expect(invitationProblems('  Julián  ', '  julian@example.com  ')).toEqual({
      fullName: null,
      email: null,
    });
  });

  it('asks for a name that is not blank', () => {
    expect(invitationProblems('', 'julian@example.com').fullName).toBe('blank');
    expect(invitationProblems('   ', 'julian@example.com').fullName).toBe('blank');
  });

  it(`refuses a name longer than ${FULL_NAME_MAX_LENGTH} characters, counted as the API does`, () => {
    expect(invitationProblems('x'.repeat(FULL_NAME_MAX_LENGTH), 'a@b.co').fullName).toBeNull();
    expect(invitationProblems('x'.repeat(FULL_NAME_MAX_LENGTH + 1), 'a@b.co').fullName).toBe(
      'too_long',
    );
    // An emoji is one character for the API, two UTF-16 units for JavaScript.
    expect(invitationProblems('😀'.repeat(FULL_NAME_MAX_LENGTH), 'a@b.co').fullName).toBeNull();
  });

  it('asks for an email that is not blank', () => {
    expect(invitationProblems('Julián', '').email).toBe('blank');
    expect(invitationProblems('Julián', '  ').email).toBe('blank');
  });

  it('refuses an email without the shape of an address', () => {
    for (const email of ['julian', 'julian@', '@example.com', 'julian@example', 'ju lian@x.co']) {
      expect(invitationProblems('Julián', email).email).withContext(email).toBe('invalid');
    }
  });

  it(`refuses an email longer than ${EMAIL_MAX_LENGTH} characters`, () => {
    const longest = `${'x'.repeat(EMAIL_MAX_LENGTH - '@example.com'.length)}@example.com`;

    expect(invitationProblems('Julián', longest).email).toBeNull();
    expect(invitationProblems('Julián', `x${longest}`).email).toBe('too_long');
  });

  it('is not valid while either field has a problem', () => {
    expect(isInvitationValid(invitationProblems('', 'julian@example.com'))).toBeFalse();
    expect(isInvitationValid(invitationProblems('Julián', 'julian'))).toBeFalse();
  });
});
