// Static analysis of the web application. Code review does not check format or
// style: Prettier formats and this file enforces everything else, including the
// architecture rules described in README.md (docs/adr/0026).
const eslint = require('@eslint/js');
const tseslint = require('typescript-eslint');
const angular = require('angular-eslint');
const importX = require('eslint-plugin-import-x');
const { createTypeScriptImportResolver } = require('eslint-import-resolver-typescript');
const prettier = require('eslint-config-prettier');

const APP = './src/app';

// Libraries that only an adapter may talk to: they are details of the outside world.
const ADAPTER_ONLY_LIBRARIES = [
  {
    name: '@angular/common/http',
    message: 'HTTP lives in infrastructure adapters (or core/http); depend on a port instead.',
  },
  { name: 'livekit-client', message: 'LiveKit lives in an infrastructure adapter behind a port.' },
  { name: 'keycloak-js', message: 'Keycloak lives in core/auth behind a port.' },
];

// Path boundaries, checked on the resolved file so that relative imports and
// aliases are treated the same way.
const BOUNDARIES = [
  // Who may depend on whom at the top level.
  {
    target: `${APP}/core`,
    from: [`${APP}/features`, `${APP}/layout`],
    message: 'core is the base of the app: it knows no feature and no layout.',
  },
  {
    target: `${APP}/shared`,
    from: [`${APP}/core`, `${APP}/features`, `${APP}/layout`],
    message: 'shared is stateless and reusable: it knows no core, layout or feature.',
  },
  {
    target: `${APP}/layout`,
    from: `${APP}/features`,
    message: 'The layout does not know the features; the router places them.',
  },
  // Layers inside a feature: dependencies point inwards.
  {
    target: `${APP}/features/*/domain/**`,
    from: [
      `${APP}/features/*/application/**`,
      `${APP}/features/*/infrastructure/**`,
      `${APP}/features/*/presentation/**`,
      `${APP}/core/**`,
      `${APP}/layout/**`,
      `${APP}/shared/ui/**`,
    ],
    message: 'The domain is pure: it only knows its own domain.',
  },
  {
    target: `${APP}/features/*/application/**`,
    from: [`${APP}/features/*/infrastructure/**`, `${APP}/features/*/presentation/**`],
    message: 'application only knows the domain and the ports it declares.',
  },
  {
    target: `${APP}/features/*/presentation/**`,
    from: `${APP}/features/*/infrastructure/**`,
    message: 'presentation never imports infrastructure; adapters are bound in app.config.ts.',
  },
  {
    target: `${APP}/features/*/infrastructure/**`,
    from: `${APP}/features/*/presentation/**`,
    message: 'infrastructure never imports presentation.',
  },
];

// A feature never imports another feature: they talk through the API or the router.
// Generated per feature because the exception is the feature itself.
const FEATURES = require('node:fs')
  .readdirSync(`${__dirname}/src/app/features`, { withFileTypes: true })
  .filter((entry) => entry.isDirectory())
  .map((entry) => entry.name);
const FEATURE_ISOLATION = FEATURES.map((feature) => ({
  target: `${APP}/features/${feature}/**`,
  from: `${APP}/features/!(${feature})/**`,
  message: 'A feature does not import another feature.',
}));

module.exports = tseslint.config(
  {
    ignores: ['dist/', 'coverage/', '.angular/', 'out-tsc/', 'runtime/', 'node_modules/'],
  },
  {
    files: ['**/*.ts'],
    extends: [
      eslint.configs.recommended,
      ...tseslint.configs.strictTypeChecked,
      ...tseslint.configs.stylisticTypeChecked,
      ...angular.configs.tsRecommended,
    ],
    languageOptions: {
      parserOptions: { projectService: true, tsconfigRootDir: __dirname },
    },
    plugins: { 'import-x': importX },
    settings: {
      'import-x/resolver-next': [createTypeScriptImportResolver({ project: './tsconfig.json' })],
    },
    processor: angular.processInlineTemplates,
    rules: {
      // Angular: selectors, signals, standalone and modern APIs.
      '@angular-eslint/directive-selector': [
        'error',
        { type: 'attribute', prefix: 'agl', style: 'camelCase' },
      ],
      '@angular-eslint/component-selector': [
        'error',
        { type: 'element', prefix: 'agl', style: 'kebab-case' },
      ],
      '@angular-eslint/prefer-inject': 'error',
      '@angular-eslint/prefer-signals': 'error',
      '@angular-eslint/prefer-output-readonly': 'error',
      '@angular-eslint/prefer-output-emitter-ref': 'error',
      '@angular-eslint/no-uncalled-signals': 'error',
      '@angular-eslint/no-async-lifecycle-method': 'error',
      '@angular-eslint/no-implicit-take-until-destroyed': 'error',
      '@angular-eslint/use-component-view-encapsulation': 'error',
      '@angular-eslint/consistent-component-styles': 'error',
      '@angular-eslint/relative-url-prefix': 'error',
      '@angular-eslint/sort-lifecycle-methods': 'error',
      '@angular-eslint/use-injectable-provided-in': 'off',

      // OnPush is the default in Angular 22; Eager would bring back dirty checking.
      'no-restricted-syntax': [
        'error',
        {
          selector:
            "MemberExpression[object.name='ChangeDetectionStrategy'][property.name='Eager']",
          message: 'Components are OnPush (the default); update state through signals.',
        },
      ],

      // Errors go through the Logger port (core/logging), never straight to the console.
      'no-console': 'error',

      // TypeScript.
      '@typescript-eslint/explicit-member-accessibility': [
        'error',
        { accessibility: 'no-public', overrides: { constructors: 'off' } },
      ],
      '@typescript-eslint/explicit-function-return-type': [
        'error',
        { allowExpressions: true, allowTypedFunctionExpressions: true },
      ],
      '@typescript-eslint/consistent-type-imports': [
        'error',
        { fixStyle: 'inline-type-imports', prefer: 'type-imports' },
      ],
      '@typescript-eslint/naming-convention': [
        'error',
        { selector: 'default', format: ['camelCase'], leadingUnderscore: 'forbid' },
        {
          selector: 'variable',
          modifiers: ['const', 'global'],
          format: ['camelCase', 'UPPER_CASE'],
        },
        { selector: 'typeLike', format: ['PascalCase'] },
        { selector: 'enumMember', format: ['PascalCase'] },
        // JSON fields of the API contract and HTTP headers keep their own spelling.
        { selector: ['objectLiteralProperty', 'typeProperty'], format: null },
        { selector: 'import', format: null },
      ],
      '@typescript-eslint/no-extraneous-class': ['error', { allowWithDecorator: true }],
      '@typescript-eslint/restrict-template-expressions': ['error', { allowNumber: true }],
      eqeqeq: ['error', 'always'],

      // Imports: order, no cycles and the architecture boundaries.
      'import-x/no-cycle': 'error',
      'import-x/no-duplicates': 'error',
      'import-x/no-default-export': 'error',
      'import-x/order': [
        'error',
        {
          groups: ['builtin', 'external', 'internal', ['parent', 'sibling', 'index']],
          pathGroups: [{ pattern: '@{core,shared,layout,features,testing}/**', group: 'internal' }],
          pathGroupsExcludedImportTypes: ['builtin'],
          'newlines-between': 'always',
          alphabetize: { order: 'asc', caseInsensitive: true },
        },
      ],
      'import-x/no-restricted-paths': ['error', { zones: [...BOUNDARIES, ...FEATURE_ISOLATION] }],
    },
  },
  {
    // Only adapters talk to the outside world.
    files: [
      'src/app/features/*/domain/**/*.ts',
      'src/app/features/*/application/**/*.ts',
      'src/app/features/*/presentation/**/*.ts',
      'src/app/layout/**/*.ts',
      'src/app/shared/**/*.ts',
    ],
    ignores: ['**/*.spec.ts'],
    rules: { 'no-restricted-imports': ['error', { paths: ADAPTER_ONLY_LIBRARIES }] },
  },
  {
    // The domain does not know the framework: plain TypeScript.
    files: ['src/app/features/*/domain/**/*.ts'],
    rules: {
      'no-restricted-imports': [
        'error',
        {
          patterns: [
            {
              group: [
                '@angular/*',
                'rxjs',
                'rxjs/*',
                '@jsverse/*',
                'livekit-client',
                'keycloak-js',
              ],
              message: 'The domain is pure TypeScript: no framework and no libraries.',
            },
          ],
        },
      ],
    },
  },
  {
    // The two places allowed to write to the console: the adapter of the Logger port
    // and the bootstrap, which runs before the logger exists.
    files: ['src/main.ts', 'src/app/core/logging/console-logger.ts'],
    rules: { 'no-console': 'off' },
  },
  {
    // Specs build doubles freely; architecture rules still apply to what they import.
    files: ['**/*.spec.ts', 'src/testing/**/*.ts'],
    rules: {
      '@typescript-eslint/no-non-null-assertion': 'off',
      '@typescript-eslint/explicit-function-return-type': 'off',
    },
  },
  {
    files: ['**/*.html'],
    extends: [...angular.configs.templateRecommended, ...angular.configs.templateAccessibility],
    rules: {
      '@angular-eslint/template/prefer-control-flow': 'error',
      '@angular-eslint/template/prefer-self-closing-tags': 'error',
      '@angular-eslint/template/prefer-ngsrc': 'error',
      '@angular-eslint/template/button-has-type': 'error',
      '@angular-eslint/template/eqeqeq': 'error',
      '@angular-eslint/template/no-any': 'error',
      '@angular-eslint/template/no-inline-styles': 'error',
      '@angular-eslint/template/use-track-by-function': 'off',
    },
  },
  // Last: turns off every rule that would fight with Prettier.
  prettier,
);
