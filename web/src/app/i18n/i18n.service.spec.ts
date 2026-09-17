import { TestBed } from '@angular/core/testing';

import en from './en.json';
import es from './es.json';
import { I18nService } from './i18n.service';

describe('I18nService', () => {
  let servicio: I18nService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    servicio = TestBed.inject(I18nService);
  });

  it('no deja ninguna clave sin traducir', () => {
    expect(Object.keys(es).sort()).toEqual(Object.keys(en).sort());
  });

  it('devuelve el texto del idioma activo', () => {
    servicio.cambiarIdioma('en');
    expect(servicio.t('estado.titulo')).toBe(en['estado.titulo']);

    servicio.cambiarIdioma('es');
    expect(servicio.t('estado.titulo')).toBe(es['estado.titulo']);
  });

  it('ante una clave ausente devuelve la clave', () => {
    expect(servicio.t('clave.que.no.existe')).toBe('clave.que.no.existe');
  });
});
