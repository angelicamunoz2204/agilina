// Static analysis of the web application.
// Code review does not check format or style: this does.
const eslint = require("@eslint/js");
const tseslint = require("typescript-eslint");
const angular = require("angular-eslint");

module.exports = tseslint.config(
  {
    files: ["**/*.ts"],
    extends: [
      eslint.configs.recommended,
      ...tseslint.configs.recommended,
      ...angular.configs.tsRecommended,
    ],
    processor: angular.processInlineTemplates,
    rules: {
      "@angular-eslint/directive-selector": [
        "error",
        { type: "attribute", prefix: "agl", style: "camelCase" },
      ],
      "@angular-eslint/component-selector": [
        "error",
        { type: "element", prefix: "agl", style: "kebab-case" },
      ],
    },
  },
  {
    // Layer rules (docs/adr/0020): presentation never imports infrastructure and
    // the domain knows no framework. The adapters are bound in app.config.ts.
    files: ["src/app/features/*/presentation/**/*.ts"],
    ignores: ["**/*.spec.ts"],
    rules: {
      "no-restricted-imports": [
        "error",
        { patterns: [{ group: ["**/infrastructure/**"], message: "Presentation must not import infrastructure; go through the application layer." }] },
      ],
    },
  },
  {
    files: ["src/app/features/*/domain/**/*.ts"],
    rules: {
      "no-restricted-imports": [
        "error",
        { patterns: [{ group: ["@angular/*", "rxjs", "rxjs/*", "**/application/**", "**/infrastructure/**", "**/presentation/**"], message: "The domain is pure: no framework and no outer layers." }] },
      ],
    },
  },
  {
    files: ["**/*.html"],
    extends: [...angular.configs.templateRecommended, ...angular.configs.templateAccessibility],
    rules: {},
  },
);
