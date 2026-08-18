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

export function GovLogos({ className = '' }: { className?: string }) {
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <img
        src={govLogos}
        alt="Department of Health · Bagong Pilipinas — Sa Bagong Pilipinas, Bawat Buhay Mahalaga"
        className="h-7 w-auto sm:h-9"
      />
      <img
        src={aspsiLogo}
        alt="Asian Social Project Services, Inc."
        className="h-7 w-auto sm:h-9"
      />
    </div>
  );
}
