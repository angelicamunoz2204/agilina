import { resolveBrowserLanguage } from './language';

describe('resolveBrowserLanguage', () => {
  it('takes the primary language of the browser', () => {
    expect(resolveBrowserLanguage('en-US')).toBe('en');
    expect(resolveBrowserLanguage('es-CO')).toBe('es');
  });

  it('falls back to Spanish for an unsupported or unknown language', () => {
    expect(resolveBrowserLanguage('fr-FR')).toBe('es');
    expect(resolveBrowserLanguage(undefined)).toBe('es');
  });
});
