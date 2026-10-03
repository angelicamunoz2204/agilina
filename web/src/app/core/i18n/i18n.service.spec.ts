import { TestBed } from '@angular/core/testing';

import en from './en.json';
import es from './es.json';
import { I18nService } from './i18n.service';

describe('I18nService', () => {
  let service: I18nService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(I18nService);
  });

  it('leaves no key untranslated', () => {
    expect(Object.keys(es).sort()).toEqual(Object.keys(en).sort());
  });

  it('returns the text of the active language', () => {
    service.setLanguage('en');
    expect(service.t('status.title')).toBe(en['status.title']);

    service.setLanguage('es');
    expect(service.t('status.title')).toBe(es['status.title']);
  });

  it('returns the key when it is missing', () => {
    expect(service.t('key.that.does.not.exist')).toBe('key.that.does.not.exist');
  });
});
