import { TEAM_NAME_MAX_LENGTH, teamNameProblem } from './team-name';

describe('teamNameProblem', () => {
  it('allows at most 80 characters, like the API', () => {
    expect(TEAM_NAME_MAX_LENGTH).toBe(80);
  });

  it('accepts a name with text', () => {
    expect(teamNameProblem('Atlas')).toBeNull();
  });

  it('finds an empty name blank', () => {
    expect(teamNameProblem('')).toBe('blank');
  });

  it('finds a name of only spaces blank', () => {
    expect(teamNameProblem('   ')).toBe('blank');
    expect(teamNameProblem('\t\n ')).toBe('blank');
  });

  it('accepts 80 characters once trimmed', () => {
    expect(teamNameProblem('x'.repeat(80))).toBeNull();
  });

  it('finds 81 characters too long', () => {
    expect(teamNameProblem('x'.repeat(81))).toBe('too_long');
  });

  it('does not count the surrounding spaces', () => {
    expect(teamNameProblem(`   ${'x'.repeat(80)}   `)).toBeNull();
  });

  it('counts an emoji as one character, as the API does', () => {
    expect(teamNameProblem('🚀'.repeat(80))).toBeNull();
    expect(teamNameProblem('🚀'.repeat(81))).toBe('too_long');
  });
});
