import { describe, expect, it } from 'vitest';
import { en } from './locales/en';
import { fil } from './locales/fil';
import { ceb } from './locales/ceb';
import { bis } from './locales/bis';
import { ilo } from './locales/ilo';
import { hil } from './locales/hil';
import { war } from './locales/war';
import { bcl } from './locales/bcl';
import { consentAug21 } from './locales/consent.aug21';

const bundles = { fil, ceb, bis, ilo, hil, war, bcl } as const;
type Loc = keyof typeof bundles;
const KEYS = ['infoStudy', 'infoPrivacy', 'infoBenefits', 'infoRights', 'contactsHeading'] as const;

describe('Aug-21 F2 consent screen (chrome consent.*)', () => {
  it('fil infoStudy is the Aug-21 Tagalog paragraph, not English', () => {
    expect(fil.consent.infoStudy).not.toEqual(en.consent.infoStudy);
    expect(fil.consent.infoStudy).not.toMatch(/requests your participation/);
    expect(fil.consent.infoStudy).toMatch(/Universal Health Care \(UHC\)/); // program names kept verbatim
  });

  it.each(Object.keys(bundles) as Loc[])(
    '%s: every generated paragraph is wired last and never echoes the English head',
    (loc) => {
      for (const k of KEYS) {
        const patch = consentAug21[loc][k];
        if (patch === undefined) continue; // no cleared paragraph -> English fallback by design
        expect(bundles[loc].consent[k]).toEqual(patch);
        expect(patch.slice(0, 60)).not.toEqual(en.consent[k].slice(0, 60));
      }
    },
  );

  it('never exceeds the anchor set (headings, buttons, raffle block stay chrome)', () => {
    for (const loc of Object.keys(bundles) as Loc[]) {
      for (const k of Object.keys(consentAug21[loc])) {
        expect(KEYS as readonly string[]).toContain(k);
      }
    }
  });

  it('leaves the chrome around the paragraphs untouched', () => {
    // The paper prints no heading, button or contact TABLE, so those stay as they were.
    for (const loc of Object.keys(bundles) as Loc[]) {
      expect(bundles[loc].consent.contactsBody).toEqual(en.consent.contactsBody);
      expect(bundles[loc].consent.continueButton).toEqual(en.consent.continueButton);
    }
  });
});
