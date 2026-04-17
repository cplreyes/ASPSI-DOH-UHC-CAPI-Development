import sharp from 'sharp';
import { mkdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.resolve(__dirname, '../public/icons');
mkdirSync(outDir, { recursive: true });

const bg = { r: 15, g: 118, b: 110, alpha: 1 }; // teal-700 #0f766e

async function solid(size, filename) {
  await sharp({
    create: { width: size, height: size, channels: 4, background: bg },
  })
    .png()
    .toFile(path.join(outDir, filename));
  console.log(`  wrote ${filename} (${size}x${size})`);
}

await solid(192, 'icon-192.png');
await solid(512, 'icon-512.png');
await solid(512, 'icon-maskable.png');
console.log('Icons generated.');
