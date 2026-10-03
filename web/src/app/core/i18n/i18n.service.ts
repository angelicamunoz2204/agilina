import { Injectable, computed, signal } from '@angular/core';

import en from './en.json';
import es from './es.json';

export type Language = 'es' | 'en';

const CATALOGS: Record<Language, Record<string, string>> = { es, en };

/**
 * Application texts in the two languages of the product.
 *
 * Language is a team attribute and comes from the API once the user has a
 * selected team; until then the browser's is used. Every user-facing text goes
 * through here: it is what makes the Definition of Done criterion verifiable
 * (it exists in Spanish and English).
 */
@Injectable({ providedIn: 'root' })
export class I18nService {
  private readonly currentLanguage = signal<Language>(this.browserLanguage());

  readonly language = this.currentLanguage.asReadonly();
  readonly catalog = computed(() => CATALOGS[this.currentLanguage()]);

  setLanguage(language: Language): void {
    this.currentLanguage.set(language);
  }

  /** Returns the text for `key`; for a missing key it returns the key, which is a
   *  visible error on screen and not a silent blank. */
  t(key: string): string {
    return this.catalog()[key] ?? key;
  }

  private browserLanguage(): Language {
    const language = typeof navigator === 'undefined' ? 'es' : navigator.language;
    return language?.toLowerCase().startsWith('en') ? 'en' : 'es';
  }
}
