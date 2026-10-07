import { expect, test, type Page } from '@playwright/test';

import { MAILPIT } from '../playwright.config';

/**
 * HU-02 and HU-03 as a person lives them: an operator invites them (`make test-e2e` did it
 * before this runs), they activate their account from the email, sign in with Keycloak and
 * land on their team; a page they open without a session takes them to sign in and brings
 * them back.
 *
 * Elements are found by their `data-testid`, which does not move when a text, a label or the
 * markup changes; what the person reads is still checked, on the element found that way.
 */
const EMAIL = process.env['E2E_EMAIL'] ?? '';
const TEAM = process.env['E2E_TEAM'] ?? '';
const PASSWORD = 'una-clave-bien-larga-1';
const KEYCLOAK_LOGIN = /localhost:8080\/realms\/agilina\/protocol\/openid-connect\/auth/;
const REFUSED = 'Correo o contraseña incorrectos.';

test.describe.configure({ mode: 'serial' });

test.beforeAll(() => {
  expect(EMAIL, 'E2E_EMAIL: run these tests with `make test-e2e`').not.toBe('');
});

/** The activation link of the invitation email, read from Mailpit (the inbox of the environment). */
async function activationLink(): Promise<string> {
  for (let attempt = 0; attempt < 20; attempt++) {
    const found = await fetch(`${MAILPIT}/api/v1/search?query=${encodeURIComponent(`to:${EMAIL}`)}`);
    const { messages } = (await found.json()) as { messages: { ID: string }[] };
    const first = messages[0];
    if (first !== undefined) {
      const message = await fetch(`${MAILPIT}/api/v1/message/${first.ID}`);
      const { Text } = (await message.json()) as { Text: string };
      const link = /https?:\/\/\S+#t=[\w-]+/.exec(Text);
      if (link !== null) {
        return link[0];
      }
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  throw new Error(`No invitation email for ${EMAIL} arrived in Mailpit`);
}

async function signInOnKeycloak(page: Page, password: string, email = EMAIL): Promise<void> {
  await page.getByTestId('login-email').fill(email);
  await page.getByTestId('login-password').fill(password);
  await page.getByTestId('login-submit').click();
}

let teamUrl = '';

test('activates the account from the link of the invitation email', async ({ page }) => {
  await page.goto(await activationLink());
  await expect(page.getByTestId('activate-title')).toHaveText('Activar cuenta');
  await expect(page).not.toHaveURL(/#t=/); // the token left the address bar once read

  const password = page.getByTestId('activate-password');
  const confirmation = page.getByTestId('activate-confirmation');
  await password.fill(PASSWORD);
  await confirmation.fill(PASSWORD);
  // Each box has its own button to see what was typed.
  await page.getByTestId('activate-password-toggle').click();
  await expect(password).toHaveAttribute('type', 'text');
  await expect(confirmation).toHaveAttribute('type', 'password');
  await page.getByTestId('activate-confirmation-toggle').click();
  await expect(confirmation).toHaveAttribute('type', 'text');
  await page.getByTestId('activate-submit').click();

  // The next stop is Keycloak's sign-in, with the email already typed.
  await expect(page).toHaveURL(KEYCLOAK_LOGIN);
  await expect(page.getByTestId('login-email')).toHaveValue(EMAIL);

  // There, too, the password can be seen while it is typed.
  const signInPassword = page.getByTestId('login-password');
  const toggle = page.getByTestId('login-password-toggle');
  await signInPassword.fill('anything');
  await toggle.click();
  await expect(signInPassword).toHaveAttribute('type', 'text');
  await expect(toggle).toHaveAttribute('aria-pressed', 'true');
});

test('a used link says so and offers a new invitation', async ({ page }) => {
  await page.goto(await activationLink());

  await expect(page.getByTestId('activate-link-problem-title')).toHaveText('Este enlace ya se usó');
  await expect(page.getByTestId('activate-request-new')).toHaveText(
    'Solicitar una invitación nueva',
  );
});

test('refused credentials get one generic message, whether or not the email exists', async ({ page }) => {
  await page.goto('/teams');
  await expect(page).toHaveURL(KEYCLOAK_LOGIN);

  await signInOnKeycloak(page, 'not-the-password');
  await expect(page.getByTestId('login-error')).toHaveText(REFUSED);

  await signInOnKeycloak(page, 'not-the-password', 'nobody@example.test');
  await expect(page.getByTestId('login-error')).toHaveText(REFUSED);
});

test('signing in from the entrance lands on the only team of the person', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveURL(KEYCLOAK_LOGIN);

  await signInOnKeycloak(page, PASSWORD);

  await expect(page).toHaveURL(/\/teams\/[0-9a-f-]{36}$/);
  await expect(page.getByTestId('team-name')).toHaveText(TEAM);
  teamUrl = page.url();
});

test('a page opened without a session asks to sign in and comes back to it', async ({ browser }) => {
  // A new browser context has no session and no cookies: it is a person arriving cold.
  const context = await browser.newContext({ locale: 'es-CO' });
  const page = await context.newPage();

  await page.goto(teamUrl);
  await expect(page).toHaveURL(KEYCLOAK_LOGIN);
  await signInOnKeycloak(page, PASSWORD);

  await expect(page.getByTestId('team-name')).toHaveText(TEAM);
  // Read once the team shows, not polled: Keycloak's answer (#state=…&code=…) must not come
  // back to the address bar after a first moment without it.
  expect(page.url()).toBe(teamUrl);
  await context.close();
});

test('the environment status stays public', async ({ browser }) => {
  const context = await browser.newContext({ locale: 'es-CO' });
  const page = await context.newPage();

  await page.goto('/status');

  await expect(page.getByTestId('status-title')).toHaveText('Estado del entorno');
  await expect(page).toHaveURL(/\/status$/);
  await context.close();
});
