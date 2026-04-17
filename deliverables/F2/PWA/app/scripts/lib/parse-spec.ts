export interface RawSection {
  id: string;
  title: string;
  body: string;
}

const SECTION_HEADER = /^## Section ([A-Z0-9]+(?:[0-9])?) — (.+?)\s*$/gm;

export function splitSections(markdown: string): RawSection[] {
  const sections: RawSection[] = [];
  const matches = [...markdown.matchAll(SECTION_HEADER)];

  for (let i = 0; i < matches.length; i++) {
    const current = matches[i];
    const next = matches[i + 1];
    const startIdx = (current.index ?? 0) + current[0].length;
    const endIdx = next ? (next.index ?? markdown.length) : markdown.length;
    const body = markdown.slice(startIdx, endIdx).trim();

    sections.push({
      id: current[1],
      title: current[2].trim(),
      body,
    });
  }

  return sections;
}
