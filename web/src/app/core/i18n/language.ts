/** Languages of the product. Same values as `Language` in agilina_shared. */
export type Language = 'es' | 'en';

export const LANGUAGES: readonly Language[] = ['es', 'en'];

export const DEFAULT_LANGUAGE: Language = 'es';

/**
 * Language to start with, from the browser's. It is provisional: the language is
 * an attribute of the team and replaces this once the team is known.
 */
export function resolveBrowserLanguage(browserLanguage: string | undefined): Language {
  const primary = browserLanguage?.toLowerCase().split('-')[0];
  return LANGUAGES.find((language) => language === primary) ?? DEFAULT_LANGUAGE;
}
