/** The address names an organization that does not exist, is suspended or is not even valid. */
export class TenantNotFoundError extends Error {
  override readonly name = 'TenantNotFoundError';
}
