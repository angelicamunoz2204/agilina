import { expect, test, type Browser, type Page } from '@playwright/test';

import { MAILPIT } from '../playwright.config';

/**
 * HU-06 as an admin lives it, in Settings → Team: the operator made them the admin of a team
 * of their own (`make test-e2e` did it before this runs, apart from the sign-in story); they
 * see the members, invite a person by email, who activates the account and joins with the
 * chosen role, change that person's role and remove them from the team. A member who opens
 * the screen by its address gets "no access": the API answers 403 and the screen only reacts.
 *
 * The sprint in progress is not walked here: no API creates sprints yet (HU-07), so the
 * integration tests cover it.
 */
const ADMIN_EMAIL = process.env['E2E_ADMIN_EMAIL'] ?? '';
const ADMIN_NAME = 'Ada Prueba';
const TEAM = process.env['E2E_ADMIN_TEAM'] ?? '';
const MEMBER_EMAIL = process.env['E2E_MEMBER_EMAIL'] ?? '';
const MEMBER_NAME = 'Mario Prueba';
const PASSWORD = 'una-clave-bien-larga-1';
const KEYCLOAK_LOGIN = /localhost:8080\/realms\/agilina\/protocol\/openid-connect\/auth/;

test.describe.configure({ mode: 'serial' });

test.beforeAll(() => {
  expect(ADMIN_EMAIL, 'E2E_ADMIN_EMAIL: run these tests with `make test-e2e`').not.toBe('');
  expect(MEMBER_EMAIL, 'E2E_MEMBER_EMAIL: run these tests with `make test-e2e`').not.toBe('');
});

/** The plain-text bodies of the emails Mailpit holds for an address, newest first. */
async function emailsTo(email: string): Promise<string[]> {
  const found = await fetch(`${MAILPIT}/api/v1/search?query=${encodeURIComponent(`to:${email}`)}`);
  const { messages } = (await found.json()) as { messages: { ID: string }[] };
  return Promise.all(
    messages.map(async ({ ID }) => {
      const message = await fetch(`${MAILPIT}/api/v1/message/${ID}`);
      return ((await message.json()) as { Text: string }).Text;
    }),
  );
}

/** Waits until an email for the address matches, and returns its text. */
async function emailMatching(email: string, matches: (text: string) => boolean): Promise<string> {
  for (let attempt = 0; attempt < 20; attempt++) {
    const text = (await emailsTo(email)).find(matches);
    if (text !== undefined) {
      return text;
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  throw new Error(`No matching email for ${email} arrived in Mailpit`);
}

const ACTIVATION_LINK = /https?:\/\/\S+\/activate#t=[\w-]+/;

async function activationLink(email: string): Promise<string> {
  const text = await emailMatching(email, (body) => ACTIVATION_LINK.test(body));
  return (ACTIVATION_LINK.exec(text) as RegExpExecArray)[0];
}

/** Activates the account from the invitation email and signs in: the person lands on their
 * only team. */
async function activateAndSignIn(page: Page, email: string): Promise<void> {
  await page.goto(await activationLink(email));
  await page.getByLabel('Contraseña', { exact: true }).fill(PASSWORD);
  await page.getByLabel('Confirmar contraseña').fill(PASSWORD);
  await page.getByRole('button', { name: 'Activar y entrar' }).click();

  await expect(page).toHaveURL(KEYCLOAK_LOGIN);
  await expect(page.getByLabel('Correo electrónico')).toHaveValue(email);
  await page.getByLabel('Contraseña').fill(PASSWORD);
  await page.getByRole('button', { name: 'Iniciar sesión' }).click();

  await expect(page).toHaveURL(/\/teams\/[0-9a-f-]{36}$/);
  await expect(page.getByRole('heading', { name: TEAM })).toBeVisible();
}

/** A browser without session or cookies: a person arriving cold. */
async function freshPage(browser: Browser): Promise<Page> {
  const context = await browser.newContext({ locale: 'es-CO' });
  return context.newPage();
}

/** The row of a member in the list, found by their email. */
function memberRow(page: Page, email: string) {
  return page.getByRole('listitem').filter({ hasText: email });
}

let page: Page;
let settingsUrl = '';

test.beforeAll(async ({ browser }) => {
  page = await freshPage(browser);
});

test.afterAll(async () => {
  await page.context().close();
});

test('the admin opens Settings → Team and sees themself as the only admin', async () => {
  await activateAndSignIn(page, ADMIN_EMAIL);

  await page.getByRole('link', { name: 'Configuración' }).click();
  await expect(page).toHaveURL(/\/teams\/[0-9a-f-]{36}\/settings$/);
  await expect(page.getByRole('heading', { name: 'Equipo', exact: true })).toBeVisible();
  settingsUrl = page.url();

  const me = memberRow(page, ADMIN_EMAIL);
  await expect(me).toContainText(ADMIN_NAME);
  await expect(me).toContainText('Administrador');
  // The only admin: the API says why the controls are off, and the screen shows it.
  await expect(page.getByLabel(`Rol de ${ADMIN_NAME}`)).toBeDisabled();
  await expect(me).toContainText('Es el único Administrador');
  await expect(
    page.getByRole('button', { name: `Eliminar a ${ADMIN_NAME} del equipo` }),
  ).toBeDisabled();
});

test('inviting someone without an account emails them the activation link', async () => {
  await page.getByRole('button', { name: 'Invitar miembro' }).click();
  const dialog = page.getByRole('dialog', { name: 'Invitar miembro' });
  await expect(dialog.getByLabel('Rol', { exact: true })).toHaveValue('member');

  await dialog.getByLabel('Nombre').fill(MEMBER_NAME);
  await dialog.getByLabel('Correo electrónico').fill(MEMBER_EMAIL);
  await dialog.getByRole('button', { name: 'Enviar invitación' }).click();

  await expect(page.getByRole('status')).toContainText('Enviamos la invitación por correo');
  expect(await activationLink(MEMBER_EMAIL)).toMatch(/\/activate#t=/);
});

test('the invited person activates the account and joins as a member, without access to the settings', async ({
  browser,
}) => {
  const memberPage = await freshPage(browser);
  await activateAndSignIn(memberPage, MEMBER_EMAIL);
  await expect(memberPage.getByRole('link', { name: 'Configuración' })).toHaveCount(0);

  // By its address: the API answers 403 and the screen says so.
  await memberPage.goto(settingsUrl);
  await expect(
    memberPage.getByRole('heading', { name: 'No tienes acceso a esta pantalla' }),
  ).toBeVisible();
  await expect(memberPage.getByLabel(`Rol de ${ADMIN_NAME}`)).toHaveCount(0);
  await memberPage.context().close();
});

test('the admin sees the new member, and inviting them again is refused', async () => {
  await page.reload();
  const member = memberRow(page, MEMBER_EMAIL);
  await expect(member).toContainText(MEMBER_NAME);
  await expect(member).toContainText('Miembro');

  await page.getByRole('button', { name: 'Invitar miembro' }).click();
  const dialog = page.getByRole('dialog', { name: 'Invitar miembro' });
  await dialog.getByLabel('Nombre').fill(MEMBER_NAME);
  await dialog.getByLabel('Correo electrónico').fill(MEMBER_EMAIL);
  await dialog.getByRole('button', { name: 'Enviar invitación' }).click();

  await expect(dialog.getByRole('alert')).toHaveText('Esta persona ya es integrante del equipo.');
  await dialog.getByRole('button', { name: 'Cancelar' }).click();
  await expect(dialog).toHaveCount(0);
});

test('the admin changes the role of the member, and back', async () => {
  const role = page.getByLabel(`Rol de ${MEMBER_NAME}`);

  await role.selectOption('admin');
  await expect(memberRow(page, MEMBER_EMAIL)).toContainText('Administrador');
  // With a second admin, the first one is no longer the last: their controls turn on.
  await expect(page.getByLabel(`Rol de ${ADMIN_NAME}`)).toBeEnabled();

  await role.selectOption('member');
  await expect(memberRow(page, MEMBER_EMAIL)).toContainText('Miembro');
  await expect(page.getByLabel(`Rol de ${ADMIN_NAME}`)).toBeDisabled();
});

test('removing the member asks first and warns they stop receiving the meetings', async () => {
  await page.getByRole('button', { name: `Eliminar a ${MEMBER_NAME} del equipo` }).click();
  const dialog = page.getByRole('dialog', { name: `¿Eliminar a ${MEMBER_NAME} del equipo?` });
  await expect(dialog).toContainText(
    'dejará de pertenecer al equipo y de recibir sus convocatorias',
  );

  await dialog.getByRole('button', { name: 'Eliminar del equipo' }).click();

  await expect(dialog).toHaveCount(0);
  await expect(memberRow(page, MEMBER_EMAIL)).toHaveCount(0);
});

test('inviting back someone who has an account adds them at once and notifies them without a link', async () => {
  await page.getByRole('button', { name: 'Invitar miembro' }).click();
  const dialog = page.getByRole('dialog', { name: 'Invitar miembro' });
  await dialog.getByLabel('Nombre').fill(MEMBER_NAME);
  await dialog.getByLabel('Correo electrónico').fill(MEMBER_EMAIL);
  await dialog.getByRole('button', { name: 'Enviar invitación' }).click();

  await expect(page.getByRole('status')).toContainText('ya tenía cuenta en Agilina');
  await expect(memberRow(page, MEMBER_EMAIL)).toContainText('Miembro');

  const notice = await emailMatching(
    MEMBER_EMAIL,
    (body) => body.includes(TEAM) && !ACTIVATION_LINK.test(body),
  );
  expect(notice).toContain('/teams/');
  expect(notice).not.toContain('#t=');
});
