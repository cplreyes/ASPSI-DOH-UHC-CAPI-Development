import coverLogos from '@/assets/brand/cover-logos.png';

// Government/agency masthead branding + PSA SSRCS clearance block, per the
// RA-approved header reference (2026-08-17). This is REGULATORY METADATA —
// rendered identically in every locale, exactly like the CSPro instruments'
// cover footers — so none of it goes through i18n.
//
// Clearance suffix -02: the PSA table numbers the cleared questionnaires
// -01 Facility Head, -03 In/Out-Patient, -04 Household
// (deliverables/CSPro/icf_content.py); -02 is the Healthcare Worker slot.
// Inferred from that documented series, not sighted on a certificate —
// flagged for ASPSI veto in the rollout note.
export const CLEARANCE_LINES = [
  'PSA SSRCS Clearance No. DOH-2651-02 | Issued July 2026 | Valid until 31 July 2027',
  'SJREB: ICF ver. 07/25/2026 | Translated Questionnaire ver. 06/05/2026',
] as const;

export function ClearanceBlock({ className = '' }: { className?: string }) {
  return (
    <div
      className={`flex flex-col gap-0.5 font-mono text-[10px] leading-tight text-muted-foreground ${className}`}
    >
      {CLEARANCE_LINES.map((line) => (
        <span key={line}>{line}</span>
      ))}
    </div>
  );
}

// THE ORDER IS FIXED BY THE CLIENT — do not rearrange these marks.
//
// #1190 (Shan, ASPSI, 2026-08-11) sets the brand-book sequence for the whole cleared
// instrument set:
//
//     DOH Seal → ASPSI → Bagong Pilipinas → Bawat Buhay Mahalaga
//
// ASPSI sits SECOND, in the "attached agency" slot, per their reference image.
//
// We now render that exact strip as ONE image, `cover-logos.png`, which is a copy of
// `deliverables/CSPro/cover_logos.png` — the same composed asset the F1/F3/F4 covers
// embed as a data-URI. It is built by `deliverables/CSPro/compose_cover_logos.py`
// from the DOH brand-book marks plus the official ASPSI mark. To change it, edit the
// inputs in `deliverables/CSPro/logos/`, re-run that script, and re-copy the output
// here — never re-cut the strip by hand, and never re-split it into separate <img>s.
//
// This corrects the 2026-08-17 masthead build, which composed the strip itself out of
// `gov-logos.png` + `aspsi.png` and so put ASPSI LAST. That `gov-logos.png` was in fact
// byte-identical to `CSPro/logos/cover_logos_doh3.png` — the PRE-composition DOH-only
// input (DOH | Bagong Pilipinas | Bawat Buhay Mahalaga), not the finished cover strip
// it was documented as. Appending ASPSI after it produced DOH → BP → BBM → ASPSI, which
// is the #1190 sequence with the agency in the wrong slot.
//
// #1281 (UAT R7): at h-7/h-9 the wordmarks inside the strip rendered ~4px tall and were
// unreadable; the reviewers asked for ~100px. That is the ceiling, not just a preference
// — cover-logos.png is 666x107, so anything past ~107px upscales and blurs, defeating the
// point. md+ therefore lands at exactly 100px (essentially 1:1), and the smaller steps
// keep the masthead usable on phones, where a full-size strip cannot share a row with the
// chrome controls. As one image the strip is also slightly NARROWER at md+ (~622px) than
// the two it replaces (~660px incl. gap), so the header row does not regress.
export function GovLogos({ className = '' }: { className?: string }) {
  return (
    <div className={`flex items-center ${className}`}>
      <img
        src={coverLogos}
        alt="Department of Health · Asian Social Project Services, Inc. · Bagong Pilipinas — Sa Bagong Pilipinas, Bawat Buhay Mahalaga"
        className="h-14 w-auto sm:h-20 md:h-[100px]"
      />
    </div>
  );
}
