const SLUG_PATTERN = /^[a-z][a-z0-9]{1,30}$/;
const RESERVED = ['platform', 'admin', 'api'];

/**
 * The name of a tenant, as the platform accepts it (AD-29): lowercase letters and digits,
 * starting with a letter, 2 to 31 characters. It becomes part of the address, so anything
 * that is not this is not a tenant and never reaches the API.
 */
export function isValidTenantSlug(slug: string): boolean {
  return SLUG_PATTERN.test(slug) && !RESERVED.includes(slug);
}
