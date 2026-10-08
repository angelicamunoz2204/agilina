import {
  areSprintFieldsValid,
  type SprintFields,
  sprintFieldsProblems,
  type SprintFieldsProblems,
} from './sprint-draft';

const VALID: SprintFields = {
  startDate: '2026-10-05',
  endDate: '2026-10-16',
  dailyTime: '09:00',
  participants: ['ana', 'bruno'],
};
const NO_PROBLEMS: SprintFieldsProblems = {
  startDate: null,
  endDate: null,
  dailyTime: null,
  participants: null,
};

describe('sprintFieldsProblems', () => {
  it('finds nothing wrong with a complete sprint', () => {
    expect(sprintFieldsProblems(VALID)).toEqual(NO_PROBLEMS);
    expect(areSprintFieldsValid(sprintFieldsProblems(VALID))).toBeTrue();
  });

  it('asks for both dates and the daily time while they are not chosen', () => {
    const problems = sprintFieldsProblems({
      ...VALID,
      startDate: '',
      endDate: '',
      dailyTime: '',
    });

    expect(problems).toEqual({
      startDate: 'blank',
      endDate: 'blank',
      dailyTime: 'blank',
      participants: null,
    });
    expect(areSprintFieldsValid(problems)).toBeFalse();
  });

  // ----------------------------------------------------------- criterion 1 --
  it('rejects an end before the start', () => {
    const problems = sprintFieldsProblems({ ...VALID, endDate: '2026-10-04' });

    expect(problems.endDate).toBe('before_start');
    expect(areSprintFieldsValid(problems)).toBeFalse();
  });

  it('compares the dates as calendar dates, across months and years', () => {
    expect(
      sprintFieldsProblems({ ...VALID, startDate: '2026-12-28', endDate: '2027-01-08' }).endDate,
    ).toBeNull();
    expect(
      sprintFieldsProblems({ ...VALID, startDate: '2027-01-08', endDate: '2026-12-28' }).endDate,
    ).toBe('before_start');
  });

  it('accepts a sprint of one day: the end on the same day as the start', () => {
    const problems = sprintFieldsProblems({
      ...VALID,
      startDate: '2026-10-05',
      endDate: '2026-10-05',
    });

    expect(problems).toEqual(NO_PROBLEMS);
  });

  it('accepts a sprint that starts and ends on a weekend: every calendar day counts', () => {
    // Saturday 2026-10-10 to Sunday 2026-10-11.
    const problems = sprintFieldsProblems({
      ...VALID,
      startDate: '2026-10-10',
      endDate: '2026-10-11',
    });

    expect(problems).toEqual(NO_PROBLEMS);
  });

  it('does not compare the end with a start that is not chosen yet', () => {
    expect(sprintFieldsProblems({ ...VALID, startDate: '' }).endDate).toBeNull();
  });

  // ----------------------------------------------------------- criterion 3 --
  it('asks for at least one participant', () => {
    const problems = sprintFieldsProblems({ ...VALID, participants: [] });

    expect(problems.participants).toBe('none');
    expect(areSprintFieldsValid(problems)).toBeFalse();
  });

  it('rejects a participant who appears twice', () => {
    const problems = sprintFieldsProblems({ ...VALID, participants: ['ana', 'bruno', 'ana'] });

    expect(problems.participants).toBe('duplicate');
    expect(areSprintFieldsValid(problems)).toBeFalse();
  });

  it('accepts a single participant', () => {
    expect(sprintFieldsProblems({ ...VALID, participants: ['ana'] }).participants).toBeNull();
  });
});

describe('areSprintFieldsValid', () => {
  (['startDate', 'endDate', 'dailyTime', 'participants'] as const).forEach((part) => {
    it(`refuses the form while ${part} has a problem`, () => {
      expect(areSprintFieldsValid({ ...NO_PROBLEMS, [part]: 'blank' })).toBeFalse();
    });
  });
});
