import { checkPasswordInput } from './password-input';

describe('checkPasswordInput', () => {
  it('accepts a password that was typed twice the same way', () => {
    expect(checkPasswordInput('a-long-password-1', 'a-long-password-1')).toBeNull();
  });

  it('asks for a password when the box is empty', () => {
    expect(checkPasswordInput('', '')).toBe('empty');
  });

  it('notices when the confirmation is different', () => {
    expect(checkPasswordInput('a-long-password-1', 'a-long-password-2')).toBe('mismatch');
    expect(checkPasswordInput('a-long-password-1', '')).toBe('mismatch');
  });
});
