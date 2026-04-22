/**
 * Generates a Keep-a-Changelog entry from conventional commits since the last
 * git tag and prepends it to CHANGELOG.md.
 *
 * Runs automatically via the `postversion` npm lifecycle hook after any
 * `npm run version:patch/minor/major` call.
 */
import { spawnSync } from 'node:child_process';
import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { join, dirname } from 'node:path';
import { createRequire } from 'node:module';

const __dirname = dirname(fileURLToPath(import.meta.url));
const require = createRequire(import.meta.url);
const pkg = require('../package.json');
const version = pkg.version;

function git(args, cwd) {
  const r = spawnSync('git', args, { encoding: 'utf8', cwd });
  if (r.error) throw r.error;
  return r.stdout.trim();
}

// Locate git root (monorepo root, not the app subfolder)
const gitRoot = git(['rev-parse', '--show-toplevel'], __dirname);

// Most recent tag, or first commit if no tags exist yet
let since;
try {
  const r = spawnSync('git', ['describe', '--tags', '--abbrev=0'], {
    encoding: 'utf8',
    cwd: gitRoot,
  });
  since = r.status === 0 ? r.stdout.trim() : null;
} catch {
  since = null;
}
if (!since) {
  since = git(['rev-list', '--max-parents=0', 'HEAD'], gitRoot);
}

const raw = git(['log', `${since}..HEAD`, '--pretty=format:%s'], gitRoot);
const commits = raw.split('\n').filter(Boolean);

const buckets = { Added: [], Fixed: [], Changed: [], Removed: [] };
const typeMap = {
  feat: 'Added',
  fix: 'Fixed',
  chore: 'Changed',
  refactor: 'Changed',
  perf: 'Changed',
  revert: 'Changed',
};

for (const msg of commits) {
  const m = msg.match(/^(feat|fix|chore|refactor|perf|revert)(\([^)]*\))?!?:\s*(.+)/);
  if (!m) continue;
  buckets[typeMap[m[1]]].push(m[3].trim());
}

const today = new Date().toISOString().split('T')[0];
let entry = `## [${version}] — ${today}\n`;
let hasContent = false;

for (const [heading, items] of Object.entries(buckets)) {
  if (!items.length) continue;
  hasContent = true;
  entry += `\n### ${heading}\n`;
  for (const item of items) entry += `- ${item}\n`;
}

if (!hasContent) entry += '\n_No conventional commits found since last tag._\n';
entry += '\n';

const changelogPath = join(__dirname, '../CHANGELOG.md');
const existing = readFileSync(changelogPath, 'utf8');

const sep = '\n---\n';
const sepIdx = existing.indexOf(sep);
if (sepIdx === -1) {
  writeFileSync(changelogPath, existing.trimEnd() + '\n\n' + entry);
} else {
  const header = existing.slice(0, sepIdx + sep.length);
  const rest = existing.slice(sepIdx + sep.length).replace(/^\n/, '');
  writeFileSync(changelogPath, header + '\n' + entry + rest);
}

console.log(`✓ CHANGELOG.md updated — v${version}`);
