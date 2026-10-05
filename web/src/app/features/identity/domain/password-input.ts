export type PasswordInputProblem = 'empty' | 'mismatch';

/**
 * What can be checked before asking the server: that something was typed and that both
 * boxes agree. The password policy itself belongs to Keycloak and is never copied here.
 */
export function checkPasswordInput(
  password: string,
  confirmation: string,
): PasswordInputProblem | null {
  if (password === '') {
    return 'empty';
  }
  return password === confirmation ? null : 'mismatch';
}
