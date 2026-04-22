// One-shot: rename Apr 08 Q-refs to Apr 20 Q-refs in hand-written files.
// Run once, then delete. Does not touch src/generated/* (already Apr 20).
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const APP_ROOT = path.resolve(__dirname, '..');

// (old, new) pairs. Sorted so that renames are applied in an order
// that prevents collisions and partial matches:
//   1. Plain renames first, old-id descending (Q114→Q125 before Q113→Q124).
//      A negative lookahead protects Q<n>.1 patterns from partial-match.
//   2. ".1" variants LAST, so their outputs (Q70, Q76, Q88) are not then
//      consumed by the plain Q70→Q79 / Q76→Q85 / Q88→Q98 renames.
const RENAMES = [
  // Plain renames, old-id descending (non-identity only)
  ['Q114', 'Q125'], ['Q113', 'Q124'], ['Q112', 'Q123'], ['Q111', 'Q122'],
  ['Q110', 'Q121'], ['Q109', 'Q120'], ['Q108', 'Q119'], ['Q107', 'Q118'],
  ['Q106', 'Q117'], ['Q105', 'Q116'], ['Q104', 'Q115'], ['Q103', 'Q114'],
  ['Q102', 'Q113'], ['Q101', 'Q112'], ['Q100', 'Q111'], ['Q99', 'Q110'],
  ['Q98', 'Q109'], ['Q97', 'Q107'], ['Q96', 'Q106'], ['Q95', 'Q105'],
  ['Q94', 'Q104'], ['Q93', 'Q103'], ['Q92', 'Q102'], ['Q91', 'Q101'],
  ['Q90', 'Q100'], ['Q89', 'Q99'], ['Q88', 'Q98'], ['Q87', 'Q97'],
  ['Q86', 'Q96'], ['Q85', 'Q95'], ['Q84', 'Q94'], ['Q83', 'Q93'],
  ['Q82', 'Q92'], ['Q81', 'Q91'], ['Q80', 'Q90'], ['Q79', 'Q89'],
  ['Q78', 'Q87'], ['Q77', 'Q86'], ['Q76', 'Q85'], ['Q75', 'Q84'],
  ['Q74', 'Q83'], ['Q73', 'Q82'], ['Q72', 'Q81'], ['Q71', 'Q80'],
  ['Q70', 'Q79'], ['Q69', 'Q78'], ['Q68', 'Q77'], ['Q67', 'Q75'],
  ['Q66', 'Q74'], ['Q65', 'Q73'], ['Q64', 'Q72'], ['Q63', 'Q71'],
  ['Q62', 'Q69'], ['Q61', 'Q68'], ['Q60', 'Q67'], ['Q59', 'Q66'],
  ['Q58', 'Q65'], ['Q57', 'Q64'], ['Q56', 'Q63'], ['Q55', 'Q62'],
  ['Q54', 'Q61'], ['Q53', 'Q60'], ['Q52', 'Q59'], ['Q51', 'Q58'],
  ['Q50', 'Q57'], ['Q49', 'Q56'], ['Q48', 'Q55'], ['Q47', 'Q54'],
  ['Q46', 'Q53'], ['Q45', 'Q52'], ['Q44', 'Q49'], ['Q43', 'Q48'],
  ['Q42', 'Q46'], ['Q41', 'Q45'], ['Q40', 'Q44'], ['Q39', 'Q43'],
  ['Q38', 'Q42'], ['Q37', 'Q41'], ['Q36', 'Q40'], ['Q35', 'Q39'],
  ['Q34', 'Q38'], ['Q33', 'Q37'], ['Q32', 'Q36'], ['Q31', 'Q35'],
  ['Q30', 'Q34'], ['Q29', 'Q33'], ['Q28', 'Q32'], ['Q27', 'Q31'],
  ['Q26', 'Q30'], ['Q25', 'Q29'], ['Q24', 'Q28'], ['Q23', 'Q27'],
  ['Q22', 'Q26'], ['Q21', 'Q25'],
  // Q13 onwards (and Q20) are identity within Section B's old range;
  // but legacyId says Q13-Q20 are identity, so no rename needed for those.

  // .1 sibling promotions (Apr 08 Q<n>.1 → proper Apr 20 sibling). LAST
  // so Q70/Q76/Q88 outputs here are not consumed by the plain pass above.
  ['Q78.1', 'Q88'],
  ['Q67.1', 'Q76'],
  ['Q62.1', 'Q70'],
];

function escRe(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

const FILES = [
  'src/lib/skip-logic.ts',
  'src/lib/skip-logic.test.ts',
  'src/lib/cross-field.ts',
  'src/lib/cross-field.test.ts',
  'src/lib/draft.test.ts',
  'src/lib/sync-client.test.ts',
  'src/lib/sync-orchestrator.test.ts',
  'src/components/survey/MultiSectionForm.tsx',
  'src/components/survey/MultiSectionForm.test.tsx',
  'src/components/survey/Question.test.tsx',
  'src/components/survey/ReviewSection.tsx',
  'src/components/survey/ReviewSection.test.tsx',
  'src/components/survey/Section.test.tsx',
  'src/App.test.tsx',
];

let totalReplacements = 0;
for (const rel of FILES) {
  const abs = path.join(APP_ROOT, rel);
  if (!fs.existsSync(abs)) {
    console.warn('SKIP (missing):', rel);
    continue;
  }
  let src = fs.readFileSync(abs, 'utf8');
  const before = src;
  let fileReplacements = 0;
  for (const [oldId, newId] of RENAMES) {
    // For ".1" variants, use exact escaping.
    // For plain Q-refs, reject matches that are the prefix of Q<n>.<digit>
    // (e.g., prevents plain Q62 from partial-matching inside Q62.1 before the
    // ".1" pass has handled it — since ".1" renames produce outputs like Q70
    // that would otherwise be clobbered by the subsequent plain Q70 rename).
    const re = oldId.includes('.')
      ? new RegExp(`\\b${escRe(oldId)}\\b`, 'g')
      : new RegExp(`\\b${oldId}(?!\\.\\d)\\b`, 'g');
    const matches = src.match(re);
    if (matches) {
      src = src.replace(re, newId);
      fileReplacements += matches.length;
    }
  }
  if (src !== before) {
    fs.writeFileSync(abs, src);
    console.log(`  ${rel}: ${fileReplacements} replacements`);
    totalReplacements += fileReplacements;
  } else {
    console.log(`  ${rel}: (unchanged)`);
  }
}
console.log(`\ntotal: ${totalReplacements} replacements across ${FILES.length} files`);
