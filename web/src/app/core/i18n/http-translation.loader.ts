import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { type Translation, type TranslocoLoader } from '@jsverse/transloco';
import { type Observable } from 'rxjs';

/**
 * Loads a catalog from public/i18n/<language>.json, relative to <base href>.
 * Only the active language is downloaded.
 */
@Injectable({ providedIn: 'root' })
export class HttpTranslationLoader implements TranslocoLoader {
  private readonly http = inject(HttpClient);

  getTranslation(language: string): Observable<Translation> {
    return this.http.get<Translation>(`i18n/${language}.json`);
  }
}
