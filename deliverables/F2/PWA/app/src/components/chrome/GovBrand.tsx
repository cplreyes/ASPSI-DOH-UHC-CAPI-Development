import govLogos from '@/assets/brand/gov-logos.png';
import aspsiLogo from '@/assets/brand/aspsi.png';

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

// #1281 (UAT R7): at h-7/h-9 the wordmarks inside the strip rendered ~4px tall and
// were unreadable. The reviewers asked for ~100px. That is the ceiling, not just a
// preference: gov-logos.png is 520x107 and aspsi.png 346x214, so anything past ~107px
// upscales and blurs — which would defeat the point. md+ therefore lands at exactly
// 100px (essentially 1:1 for the gov strip), and the smaller steps keep the masthead
// usable on phones, where a 100px strip would not fit beside the chrome controls.
export function GovLogos({ className = '' }: { className?: string }) {
  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <img
        src={govLogos}
        alt="Department of Health · Bagong Pilipinas — Sa Bagong Pilipinas, Bawat Buhay Mahalaga"
        className="h-14 w-auto sm:h-20 md:h-[100px]"
      />
      <img
        src={aspsiLogo}
        alt="Asian Social Project Services, Inc."
        className="h-14 w-auto sm:h-20 md:h-[100px]"
      />
    </div>
  );
}
