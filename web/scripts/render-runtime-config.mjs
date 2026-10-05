// Renders runtime-config.template.json into runtime/config.json from the
// environment, for `ng serve`. In production nginx renders the same template with
// envsubst when the container starts (see the Dockerfile), so one image serves
// every environment and no URL is compiled into the bundle.
//
// It fails when a variable is missing: a half-configured app is worse than one
// that does not start.
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const templatePath = resolve(root, 'runtime-config.template.json');
const outputPath = resolve(root, 'runtime/config.json');
const placeholder = /\$\{([A-Z0-9_]+)\}/g;

const template = readFileSync(templatePath, 'utf8');
const missing = [...template.matchAll(placeholder)]
  .map(([, name]) => name)
  .filter((name) => !process.env[name]);

if (missing.length > 0) {
  console.error(`Missing environment variables for the web runtime config: ${missing.join(', ')}`);
  process.exit(1);
}

// JSON.stringify escapes the value; slice drops the quotes it adds.
const rendered = template.replace(placeholder, (_, name) =>
  JSON.stringify(process.env[name]).slice(1, -1),
);
mkdirSync(dirname(outputPath), { recursive: true });
writeFileSync(outputPath, rendered);
console.log(`Runtime config written to ${outputPath}`);
