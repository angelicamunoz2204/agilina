import en from '../../../../public/i18n/en.json';
import es from '../../../../public/i18n/es.json';

/** Every key as a dotted path, the way templates use it. */
function flatten(catalog: object, prefix = ''): Record<string, unknown> {
  return Object.entries(catalog as Record<string, unknown>).reduce<Record<string, unknown>>(
    (keys, [key, value]) => {
      const path = prefix === '' ? key : `${prefix}.${key}`;
      return typeof value === 'object' && value !== null
        ? { ...keys, ...flatten(value, path) }
        : { ...keys, [path]: value };
    },
    {},
  );
}

describe('i18n catalogs', () => {
  const spanish = flatten(es);
  const english = flatten(en);

  it('leave no key untranslated in either language', () => {
    expect(Object.keys(english).sort()).toEqual(Object.keys(spanish).sort());
  });

  it('have no empty text', () => {
    const empty = [
      ...Object.entries(spanish).map(([key, text]) => [`es:${key}`, text] as const),
      ...Object.entries(english).map(([key, text]) => [`en:${key}`, text] as const),
    ]
      .filter(([, text]) => typeof text !== 'string' || text.trim() === '')
      .map(([key]) => key);
    expect(empty).toEqual([]);
  });
});
