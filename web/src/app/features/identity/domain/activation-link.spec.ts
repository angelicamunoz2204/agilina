import { readActivationToken } from './activation-link';

describe('readActivationToken', () => {
  it('reads the token from the fragment of the link', () => {
    expect(readActivationToken('t=abc-DEF_123')).toBe('abc-DEF_123');
  });

  it('finds the token among other parameters', () => {
    expect(readActivationToken('x=1&t=abc')).toBe('abc');
  });

  [null, '', 't=', 't=%20%20', 'other=abc', 'abc'].forEach((fragment) => {
    it(`finds nothing in ${JSON.stringify(fragment)}`, () => {
      expect(readActivationToken(fragment)).toBeNull();
    });
  });
});
