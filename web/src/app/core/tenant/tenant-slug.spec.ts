import { isValidTenantSlug } from './tenant-slug';

describe('isValidTenantSlug', () => {
  ['acme', 'ecomoda', 'ab', 'a1', 'a' + 'b'.repeat(30)].forEach((slug) => {
    it(`accepts ${slug}`, () => {
      expect(isValidTenantSlug(slug)).toBeTrue();
    });
  });

  ['', 'a', 'a' + 'b'.repeat(31), '1acme', 'Acme', 'ac-me', 'ac_me', 'not-found', 'ácme'].forEach(
    (slug) => {
      it(`rejects ${JSON.stringify(slug)}`, () => {
        expect(isValidTenantSlug(slug)).toBeFalse();
      });
    },
  );

  ['platform', 'admin', 'api'].forEach((slug) => {
    it(`keeps ${slug} for the platform`, () => {
      expect(isValidTenantSlug(slug)).toBeFalse();
    });
  });
});
