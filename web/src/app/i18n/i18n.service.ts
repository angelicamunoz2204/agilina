import { Injectable, computed, signal } from '@angular/core';

import en from './en.json';
import es from './es.json';

export type Idioma = 'es' | 'en';

const CATALOGOS: Record<Idioma, Record<string, string>> = { es, en };

/**
 * Textos de la aplicación en los dos idiomas del producto.
 *
 * El idioma es un atributo del equipo y llega de la API cuando el usuario ya
 * tiene equipo seleccionado; hasta entonces se usa el del navegador. Todo
 * texto dirigido al usuario pasa por aquí: es lo que hace verificable el
 * criterio del Definition of Done de que exista en español y en inglés.
 */
@Injectable({ providedIn: 'root' })
export class I18nService {
  private readonly idiomaActual = signal<Idioma>(this.idiomaDelNavegador());

  readonly idioma = this.idiomaActual.asReadonly();
  readonly catalogo = computed(() => CATALOGOS[this.idiomaActual()]);

  cambiarIdioma(idioma: Idioma): void {
    this.idiomaActual.set(idioma);
  }

  /** Devuelve el texto de `clave`; ante una clave ausente devuelve la clave, que es
   *  un error visible en pantalla y no un espacio en blanco silencioso. */
  t(clave: string): string {
    return this.catalogo()[clave] ?? clave;
  }

  private idiomaDelNavegador(): Idioma {
    const idioma = typeof navigator === 'undefined' ? 'es' : navigator.language;
    return idioma?.toLowerCase().startsWith('en') ? 'en' : 'es';
  }
}
