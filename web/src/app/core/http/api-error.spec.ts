import { readApiError } from './api-error';

describe('readApiError', () => {
  it('reads the code, the reasons and the request id of the common body', () => {
    const body = {
      error: {
        status: 422,
        code: 'password_policy',
        message: 'The password breaks the policy.',
        details: { reasons: ['min_length', 'digits'] },
        request_id: 'c1b9f0a2e47d4c1f',
      },
    };

    expect(readApiError(body)).toEqual({
      code: 'password_policy',
      reasons: ['min_length', 'digits'],
      requestId: 'c1b9f0a2e47d4c1f',
    });
  });

  it('answers no reasons when the error has no details', () => {
    expect(readApiError({ error: { code: 'not_authenticated' } })?.reasons).toEqual([]);
  });

  it('ignores reasons that are not text', () => {
    expect(
      readApiError({ error: { code: 'x', details: { reasons: ['a', 1, null] } } })?.reasons,
    ).toEqual(['a']);
  });

  it('is undefined when the body is not an error of the API', () => {
    expect(readApiError(null)).toBeUndefined();
    expect(readApiError('<html>502</html>')).toBeUndefined();
    expect(readApiError({ detail: 'Not Found' })).toBeUndefined();
    expect(readApiError({ error: { message: 'no code' } })).toBeUndefined();
  });
});
