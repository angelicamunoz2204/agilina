import { type EnvironmentProviders, importProvidersFrom } from '@angular/core';
import { TranslocoTestingModule } from '@jsverse/transloco';

import en from '../../public/i18n/en.json';
import es from '../../public/i18n/es.json';

/**
 * Real catalogs, loaded synchronously. Tests assert on the Spanish text so that
 * a missing or renamed key shows up as a failing test.
 */
export function provideTestI18n(): EnvironmentProviders {
  return importProvidersFrom(
    TranslocoTestingModule.forRoot({
      langs: { es, en },
      translocoConfig: { availableLangs: ['es', 'en'], defaultLang: 'es' },
      preloadLangs: true,
    }),
  );
}
