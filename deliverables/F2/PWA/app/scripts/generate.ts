#!/usr/bin/env tsx
/**
 * F2 PWA generator.
 *
 * Reads spec/F2-Spec.md, emits src/generated/items.ts + src/generated/schema.ts.
 * Invoke: `npm run generate`
 */

import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import { parseSpec } from './lib/parse-spec';
import { emitItems } from './lib/emit-items';
import { emitSchema } from './lib/emit-schema';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const APP_ROOT = resolve(__dirname, '..');
const SPEC_PATH = resolve(APP_ROOT, 'spec/F2-Spec.md');
const GEN_DIR = resolve(APP_ROOT, 'src/generated');
const ITEMS_PATH = resolve(GEN_DIR, 'items.ts');
const SCHEMA_PATH = resolve(GEN_DIR, 'schema.ts');

async function main(): Promise<void> {
  const markdown = readFileSync(SPEC_PATH, 'utf-8');
  const result = parseSpec(markdown);

  const supportedCount = result.sections.reduce((n, s) => n + s.items.length, 0);
  console.log(
    `generator: ${result.sections.length} section(s), ${supportedCount} supported item(s), ${result.unsupported.length} unsupported.`,
  );

  mkdirSync(GEN_DIR, { recursive: true });
  writeFileSync(ITEMS_PATH, emitItems(result), 'utf-8');
  writeFileSync(SCHEMA_PATH, emitSchema(result), 'utf-8');

  console.log(`  wrote ${ITEMS_PATH}`);
  console.log(`  wrote ${SCHEMA_PATH}`);

  if (result.unsupported.length > 0) {
    console.log('\ngenerator: unsupported items (skipped):');
    for (const u of result.unsupported) {
      console.log(`  - ${u.section}.${u.id} (${u.rawType}): ${u.reason}`);
    }
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
