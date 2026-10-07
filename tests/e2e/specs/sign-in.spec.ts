import { expect, test, type Page } from '@playwright/test';

import { MAILPIT } from '../playwright.config';

/**
 * HU-02, HU-03 and the multitenancy of AD-29 as a person lives them. Every tenant is an
 * organization with its own database, its own realm and its own login: the same person (the
 * same email) invited to two tenants has two separate accounts. `make test-e2e` invites her to
 * both before this runs. In each tenant she activates her account from the email, signs in with
 * Keycloak and lands on her team; a page she opens without a session takes her to sign in and
 * brings her back. Then the tenants are shown not to mix.
 */
const RUN = process.env['E2E_RUN'] ?? '';
const EMAIL = `e2e-${RUN}@example.test`;
const PASSWORD = 'una-clave-bien-larga-1';
const REFUSED = 'Correo o contraseña incorrectos.';
const TENANTS = ['acme', 'ecomoda'] as const;

const keycloakLogin = (tenant: string): RegExp =>
  new RegExp(`localhost:8080/realms/agilina-${tenant}/protocol/openid-connect/auth`);
const teamName = (tenant: string): string => `E2E ${RUN} ${tenant}`;

test.beforeAll(() => {
  expect(RUN, 'E2E_RUN: run these tests with `make test-e2e`').not.toBe('');
});

/** The activation link of the invitation to ``tenant``, read from Mailpit (the inbox of the
 * environment). The same address was invited to both tenants: the link names which. */
async function activationLink(tenant: string): Promise<string> {
  for (let attempt = 0; attempt < 20; attempt++) {
    const found = await fetch(`${MAILPIT}/api/v1/search?query=${encodeURIComponent(`to:${EMAIL}`)}`);
    const { messages } = (await found.json()) as { messages: { ID: string }[] };
    for (const { ID } of messages) {
      const message = await fetch(`${MAILPIT}/api/v1/message/${ID}`);
      const { Text } = (await message.json()) as { Text: string };
      const link = new RegExp(`https?://\\S+/${tenant}/activate#t=[\\w-]+`).exec(Text);
      if (link !== null) {
        return link[0];
      }
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  throw new Error(`No invitation email for ${EMAIL} to ${tenant} arrived in Mailpit`);
}

async function signInOnKeycloak(page: Page, password: string, email = EMAIL): Promise<void> {
  await page.getByLabel('Correo electrónico').fill(email);
  await page.getByLabel('Contraseña').fill(password);
  await page.getByRole('button', { name: 'Iniciar sesión' }).click();
}

for (const tenant of TENANTS) {
  test.describe(`the tenant ${tenant}`, () => {
    test.describe.configure({ mode: 'serial' });

    let teamUrl = '';

    test('has no account for her until she activates it', async ({ page }) => {
      await page.goto(`/${tenant}/teams`);
      await expect(page).toHaveURL(keycloakLogin(tenant));

      await signInOnKeycloak(page, PASSWORD);

      await expect(page.getByRole('alert')).toHaveText(REFUSED);
    });

    test('activates the account from the link of the invitation email', async ({ page }) => {
      await page.goto(await activationLink(tenant));
      await expect(page.getByRole('heading', { name: 'Activar cuenta' })).toBeVisible();
      await expect(page).not.toHaveURL(/#t=/); // the token left the address bar once read

      await page.getByLabel('Contraseña', { exact: true }).fill(PASSWORD);
      await page.getByLabel('Confirmar contraseña').fill(PASSWORD);
      await page.getByRole('button', { name: 'Activar y entrar' }).click();

      // The next stop is the sign-in of this tenant's realm, with the email already typed.
      await expect(page).toHaveURL(keycloakLogin(tenant));
      await expect(page.getByLabel('Correo electrónico')).toHaveValue(EMAIL);
    });

    test('a used link says so and offers a new invitation', async ({ page }) => {
      await page.goto(await activationLink(tenant));

      await expect(page.getByRole('heading', { name: 'Este enlace ya se usó' })).toBeVisible();
      await expect(
        page.getByRole('button', { name: 'Solicitar una invitación nueva' }),
      ).toBeVisible();
    });

    test('refused credentials get one generic message, whether or not the email exists', async ({
      page,
    }) => {
      await page.goto(`/${tenant}/teams`);
      await expect(page).toHaveURL(keycloakLogin(tenant));

      await signInOnKeycloak(page, 'not-the-password');
      await expect(page.getByRole('alert')).toHaveText(REFUSED);

      await signInOnKeycloak(page, 'not-the-password', 'nobody@example.test');
      await expect(page.getByRole('alert')).toHaveText(REFUSED);
    });

    test('signing in from the entrance lands on the only team of the person', async ({ page }) => {
      await page.goto(`/${tenant}`);
      await expect(page).toHaveURL(keycloakLogin(tenant));

      await signInOnKeycloak(page, PASSWORD);

      await expect(page).toHaveURL(new RegExp(`/${tenant}/teams/[0-9a-f-]{36}$`));
      await expect(page.getByRole('heading', { name: teamName(tenant) })).toBeVisible();
      teamUrl = page.url();
    });

    test('a page opened without a session asks to sign in and comes back to it', async ({
      browser,
    }) => {
      // A new browser context has no session and no cookies: it is a person arriving cold.
      const context = await browser.newContext({ locale: 'es-CO' });
      const page = await context.newPage();

      await page.goto(teamUrl);
      await expect(page).toHaveURL(keycloakLogin(tenant));
      await signInOnKeycloak(page, PASSWORD);

      await expect(page).toHaveURL(teamUrl);
      await expect(page.getByRole('heading', { name: teamName(tenant) })).toBeVisible();
      await context.close();
    });

    test('the environment status stays public', async ({ browser }) => {
      const context = await browser.newContext({ locale: 'es-CO' });
      const page = await context.newPage();

      await page.goto(`/${tenant}/status`);

      await expect(page.getByRole('heading', { name: 'Estado del entorno' })).toBeVisible();
      await expect(page).toHaveURL(new RegExp(`/${tenant}/status$`));
      await context.close();
    });
  });
}

test.describe('the tenants do not mix', () => {
  test('the team of one tenant is not found in the other', async ({ browser }) => {
    // She is signed in to acme, with her team's address; the same address under ecomoda is
    // another tenant: it asks for the login of ecomoda, and after it the team does not exist.
    const context = await browser.newContext({ locale: 'es-CO' });
    const page = await context.newPage();
    await page.goto('/acme');
    await signInOnKeycloak(page, PASSWORD);
    await expect(page).toHaveURL(/\/acme\/teams\/[0-9a-f-]{36}$/);
    const acmeTeamId = /teams\/([0-9a-f-]{36})$/.exec(page.url())?.[1] ?? '';

    await page.goto(`/ecomoda/teams/${acmeTeamId}`);
    await expect(page).toHaveURL(keycloakLogin('ecomoda'));
    await signInOnKeycloak(page, PASSWORD);

    await expect(page).toHaveURL(new RegExp(`/ecomoda/teams/${acmeTeamId}$`));
    await expect(page.getByRole('heading', { name: teamName('acme') })).toHaveCount(0);
    await context.close();
  });

  test('an address that names no organization is not found', async ({ page }) => {
    for (const address of ['/', '/nobody', '/nobody/teams', '/Acme/teams']) {
      await page.goto(address);
      await expect(
        page.getByRole('heading', { name: 'No encontramos esta organización' }),
      ).toBeVisible();
    }
  });
});
