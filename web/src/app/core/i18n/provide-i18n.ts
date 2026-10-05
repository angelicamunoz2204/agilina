import { DOCUMENT } from '@angular/common';
import {
  type EnvironmentProviders,
  inject,
  isDevMode,
  makeEnvironmentProviders,
  provideEnvironmentInitializer,
} from '@angular/core';
import {
  provideTransloco,
  provideTranslocoMissingHandler,
  TranslocoService,
} from '@jsverse/transloco';

import { HttpTranslationLoader } from './http-translation.loader';
import { LANGUAGES, resolveBrowserLanguage } from './language';
import { LoggingMissingHandler } from './logging-missing-handler';

/** Transloco with the catalogs of public/i18n and the language of the browser. */
export function provideI18n(): EnvironmentProviders {
  return makeEnvironmentProviders([
    provideTransloco({
      config: {
        availableLangs: [...LANGUAGES],
        defaultLang: resolveBrowserLanguage(globalThis.navigator.language),
        reRenderOnLangChange: true,
        prodMode: !isDevMode(),
        missingHandler: { useFallbackTranslation: false, logMissingKey: false },
      },
      loader: HttpTranslationLoader,
    }),
    provideTranslocoMissingHandler(LoggingMissingHandler),
    // Screen readers and the browser's spell checker read <html lang>.
    provideEnvironmentInitializer(() => {
      const document = inject(DOCUMENT);
      inject(TranslocoService).langChanges$.subscribe((language) => {
        document.documentElement.lang = language;
      });
    }),
  ]);
}
