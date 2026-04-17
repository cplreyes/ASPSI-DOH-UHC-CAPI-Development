#!/usr/bin/env tsx
/**
 * F2 PWA generator entrypoint.
 *
 * Reads spec/F2-Spec.md, emits src/generated/items.ts + src/generated/schema.ts.
 *
 * Invoke: `npm run generate`
 */

async function main(): Promise<void> {
  console.log('generator: stub — parsing + emitting land in tasks 5–11');
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
