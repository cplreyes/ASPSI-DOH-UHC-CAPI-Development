// Bisaya bundle — app chrome DRAFT (machine-assisted, pending ASPSI QC). Survey content is NOT here; it lives in spec/translations/bis.json.
import type { EnBundle } from './en';

export const bis: EnBundle = {
  chrome: {
    appTitle: 'UHC Survey Y2 — Healthcare Worker Survey Questionnaire',
    install: 'I-install',
    loading: 'Nagkarga…',
    formView: 'Form',
    syncView: 'Sync',
    thankYouHeading: 'Salamat',
    thankYouBody: 'Ang imong tubag natipigan na niini nga device ug mag-sync kini kung naka-online na ang app.',
    // Sync-on-submit delivery gate (design F2-Facility-Slug-Links-2026-07-16) —
    // English until the ASPSI translation pass delivers dialect wording.
    delivering: 'Submitting…',
    deliveredBody: 'Submitted ✓ — your response is in. You can close this page.',
    deliveryOffline: 'Saved on this phone — it will send automatically when you are back online.',
    deliveryFailed:
      'Your response is saved on this device but could not be sent automatically. Please show this screen to ASPSI staff.',
    startNewSurvey: 'Pagsugod og bag-ong survey',
    submitFailedHeading: 'Napakyas ang pagpasa',
    submitFailedBody:
      'Wala matipigi ang imong tubag. I-tap ang retry aron sulayan pag-usab. Kung magpadayon ang problema, ang imong draft naa pa gihapon sa miaging screen.',
    submitFailedRetry: 'Sulayi pag-usab',
    submitBlockedKillSwitch:
      'Temporaryong gipahunong sa administrator ang pagpasa. Ang imong progreso natipigan nang lokal ug mag-sync kini kung magpadayon na ang pagpasa.',
    submitBlockedSpecDrift: 'Adunay gikinahanglan nga update sa app. Palihog i-reload una mopasa.',
    killSwitchTitle: 'Temporaryong gipahunong ang pagpasa',
    killSwitchBody:
      'Gipahunong sa administrator ang pagpasa. Ang imong progreso natipigan nang lokal ug mag-sync kini kung magpadayon na ang pagpasa.',
    specDriftTitle: 'Gikinahanglan ang update',
    specDriftBody:
      'Mas daan ang bersyon sa imong form ({{localVersion}}) kaysa sa gikinahanglan sa server ({{serverMin}}). I-reload aron makuha ang pinakabag-o.',
    reload: 'I-reload',
  },
  language: {
    label: 'Pinulongan',
    en: 'English',
    fil: 'Filipino',
  },
  enrollment: {
    heading: 'Pag-enroll',
    helper:
      'Isulod ang imong HCW ID ug pilia ang imong pasilidad. Mausab nimo kini sa ulahi gikan sa Sync page.',
    hcwIdLabel: 'HCW ID',
    facilityLabel: 'Pasilidad',
    facilityPlaceholder: 'Pagpili og pasilidad…',
    noFacilitiesCached: 'Walay naka-cache nga pasilidad. I-tap ang Refresh aron i-download ang master list.',
    enrollButton: 'Pag-enroll',
    refreshButton: 'I-refresh ang listahan sa pasilidad',
    refreshingButton: 'Nag-refresh…',
    changeButton: 'Usbon ang enrollment',
    changeConfirm: 'Mo-sign out niini nga device? Makapag-enroll ka pag-usab pagkahuman.',
    changeConfirmWithDraft:
      'Aduna kay wala mahuman nga draft. Ang pag-usab sa enrollment magtangtang niini. Mopadayon?',
    tokenStep: 'Lakang 1: Tablet token',
    tokenHelper:
      'I-paste ang token gikan sa imong ASPSI ops contact. Gihimo nila kini alang niini nga tablet panahon sa provisioning.',
    tokenLabel: 'Tablet token',
    tokenPlaceholder: 'eyJhbGc...',
    verifyTokenButton: 'I-verify ang token',
    verifyingTokenButton: 'Nag-verify…',
    tokenInvalid: 'Sayop ang pagkahimo sa token. Makig-uban sa ASPSI ops alang sa bag-o.',
    tokenRevoked: 'Na-revoke na kini nga tablet. Makig-uban sa ASPSI ops.',
    tokenOffline: 'Offline ka. Susiha ang imong koneksyon ug sulayi pag-usab.',
    identityStep: 'Lakang 2: Ila-ila ang imong kaugalingon',
    tokenAccepted: 'Gidawat ang token alang sa pasilidad nga {{facility}}. Pilia ang imong kaugalingon sa roster sa ubos.',
    // Model C — open self-register (English pending translation).
    selfRegisterIntro: "Tap Start to begin. You'll be given a number, then answer the survey on this phone.",
    selfRegisterStart: "Start — I'm a healthcare worker here",
    selfRegisterBusy: 'Assigning your number…',
    selfRegisterReceiptHeading: 'You are enrolled',
    selfRegisterReceipt: 'You are respondent {{qn}}. Tap Continue to begin the survey.',
    selfRegisterContinue: 'Continue',
    selfRegisterFailed: 'Could not register right now. Check your connection and try again.',
  },
  claim: {
    heading: 'Opening your survey…',
    claiming: 'Setting up your questionnaire — one moment.',
    invalidLink: 'This link is invalid or has expired. Please ask ASPSI ops for a new one.',
    alreadyDone: 'This survey has already been completed. Thank you.',
    offline: "You're offline. Check your connection and tap Retry.",
    unavailable: 'The survey is temporarily unavailable. Please try again shortly.',
    retry: 'Retry',
  },
  // Facility slug links (design F2-Facility-Slug-Links-2026-07-16) — English
  // until the ASPSI translation pass delivers dialect wording.
  facilityStart: {
    resolvingHeading: 'Opening the survey…',
    resolving: 'Checking this link — one moment.',
    heading: '{{facility}} — HCW Survey',
    intro: 'Your answers are voluntary and anonymous. Tap Start to begin on this phone.',
    start: 'Start the survey',
    starting: 'Setting up your questionnaire…',
    inactive: "This survey link isn't active. Please check with ASPSI ops.",
    offline: "You're offline. Check your connection and tap Retry.",
    unavailable: 'The survey is temporarily unavailable. Please try again shortly.',
    retry: 'Retry',
    noLinkHeading: 'Open your facility survey link',
    noLinkBody:
      'This survey opens from a facility link that looks like uhc-hcw.asiansocial.org/f/your-facility. Ask ASPSI staff for your facility link.',
  },
  navigator: {
    // #809 — English until the ASPSI translation pass delivers dialect wording.
    requiredIncomplete: 'Some required (*) questions are unanswered. Please complete them to continue.',
    previous: 'Miagi',
    next: 'Sunod',
    submit: 'Ipasa',
    saveDraft: 'I-save ang Draft',
    draftSaved: 'Na-save ang draft',
    sectionLocked: 'Kompletoha ang mga seksyon sumala sa han-ay — humana usa ang kasamtangang seksyon.',
  },
  progressBar: {
    sectionLabel: 'Seksyon {{current}} sa {{total}}',
  },
  question: {
    requiredFallback: 'Gikinahanglan kini nga field.',
    pleaseSpecifyLabel: 'Palihog ipasabot',
    pleaseSpecifyError: 'Palihog ipasabot',
    selectAllThatApply: 'Pilia tanan nga mohaom.',
    // English draft pending ASPSI QC (R3 #306 Q35 partial-date UI).
    partialDate: {
      year: 'Year',
      month: 'Month',
      day: 'Day',
      optional: 'Optional',
    },
  },
  review: {
    heading: 'Susiha ang imong mga tubag',
    crossFieldRegion: 'Mga pahimangno sa cross-field',
    sectionHeading: 'Seksyon {{id}} — {{title}}',
    edit: 'I-edit',
    submit: 'Ipasa',
    // English draft pending ASPSI QC (R3 #305 hard-block message).
    blockingError: 'Please resolve the highlighted issue above before submitting.',
  },
  // #838 — tool-usability feedback (pretest). English pending ASPSI translation;
  // wording is ASPSI's call, so it is NOT localized here.
  feedback: {
    heading: 'Before you submit',
    note: 'This is about the survey tool itself, not your answers. It helps us improve it.',
    easeQuestion: 'Did you find the survey tool easy to use and navigate?',
    easeRequired: 'Please answer this question before submitting.',
    yes: 'Yes',
    no: 'No',
    whyLabel: 'Why or why not?',
    whyPlaceholder: 'Optional — tell us anything that was confusing or worked well.',
  },
  consent: {
    // #808 consent gate — English until the ASPSI translation pass delivers dialect wording.
    heading: 'Informed Consent — Please Read Carefully',
    infoHeading: 'Part I — Information about the study',
    intro:
      'Before answering the survey, please read the information below. If you understand and agree to participate, you will be asked to confirm your consent at the end of this section. Your consent confirmation is recorded with your survey response.',
    // #1313 (2026-08-25): infoStudy — EN pending translation; the English master changed
    // with the Aug-17 paper and no cleared bis translation exists yet.
    infoStudy:
      'The Asian Social Project Services, Inc. (ASPSI) requests your participation in a study on Universal Health Care (UHC). This study aims to generate evidence on the overall experience of the healthcare service providers and the general public to support continuous monitoring, evaluation, and learning of the implementation of the UHC Act, its Implementing Rules and Regulations (IRR), and packages of programs like Yaman ng Kalusugan Program (YAKAP), No Balance Billing (NBB), Zero Balance Billing (ZBB), Bagong Urgent Care and Ambulatory Services (BUCAS) centers, and Guaranteed and Accessible Medications for Outpatient Treatment (GAMOT). The Department of Health funded this study. The survey may take more or less than an hour to complete. The questions will cover your professional profile, UHC awareness, changes in facility operations since 2019, specialized programs (YAKAP/Konsulta, NBB/ZBB, BUCAS, GAMOT), referral systems, professional fee charging, task sharing, and your overall job satisfaction, including compensation, work environment, and professional development opportunities. Your progress is saved automatically on this device — you can pause and continue at any time before submitting.',
    infoPrivacy:
      'We are committed to protecting your privacy. If you choose to participate, we will never share your information outside of the study team. We will never include your name in information shared with the government or in any reports. Your name will be kept separately from your answers in a private, secure location. For this survey, we also ask that you respect the privacy of your colleagues and patients and do not share anything you discuss here. With all research, there is a small chance that someone else might get to see your data. We try our best to prevent that, but if it happens, we will tell you as soon as possible.',
    // #1313 (2026-08-25): infoBenefits — EN pending translation; the English master changed
    // with the Aug-17 paper and no cleared bis translation exists yet.
    infoBenefits:
      "Aside from this, there are no other risks to you if you take part in this study. As a benefit of the research, the knowledge gained may help the government and DOH better support your healthcare needs. The survey may take more or less than an hour, and participating in this survey will also enter you into a raffle, giving you a chance to win PhP 1,000 as a way of thanking you for the time you have shared with us.",
    infoRights:
      'You are free to decline participation or to stop at any time before submitting the form. Choosing not to participate will not result in any penalty, and you will not have to pay anything to take part in this study.',
    contactsHeading:
      'If you have concerns or questions about your rights as a participant, you can contact:',
    // aug17 migration (Task 3.1, 2026-08-19): English placeholder mirrors
    // en.ts (chrome-bundle mirror rule) — synced ethics-contact details.
    contactsBody:
      'Single Joint Research Ethics Board (SJREB), Department of Health\nEmail: sjreb@doh.gov.ph\nTel: (02) 8651-7800 local 1326, 1328\n\nDepartment of Health\nName: Lindsley Jeremiah D. Villarante\nEmail: ldvillarante@doh.gov.ph\nTel: +63 (02) 8651-7800 local 1432\n\nAsian Social Project Services, Inc.\nName: Paulyn Jean A. Claro\nEmail: inquiry.aspsi.doh.uhc.survey2@gmail.com\nTel: +63 917 819 6884',
    confirmHeading: 'Consent confirmation',
    confirmPrompt:
      'Please confirm whether you have read and understood the information above and whether you agree to participate in this survey. You must confirm to proceed.',
    agreeOption:
      'I have read and understood the information above. I voluntarily agree to participate in this survey.',
    declineOption: 'I do not wish to participate.',
    continueButton: 'Continue',
    // #1002 raffle-phone strings — EN pending the next translation re-key batch.
    rafflePhoneHeading: 'Raffle contact number (optional)',
    rafflePhoneNote:
      'If you would like to join the raffle, you may enter a phone number below. It will only be used to contact you if you win the raffle. A GCash number is preferred, as it will be used both for contacting you and for sending your prize.',
    rafflePhoneLabel: 'Phone number',
    rafflePhonePlaceholder: 'e.g. 09XX XXX XXXX (GCash preferred)',
    rafflePhoneConfirmHeading: 'No contact number provided',
    rafflePhoneConfirmBody:
      'You have not provided a contact number. Without a contact number, you will not be eligible to receive the raffle prize if selected as a winner. Do you want to proceed?',
    rafflePhoneConfirmBack: 'Go back',
    rafflePhoneConfirmProceed: 'Proceed without a number',
    declinedHeading: 'Thank you for your time',
    declinedBody:
      'You chose not to participate in this survey. No survey questions will be shown and no response has been recorded on this device. If this was a mistake, you can start over below.',
    startOver: 'Start over',
    gps_disclosure:
      'Kung mopasa ka, irekord ang lokasyon sa imong device aron ma-map sa DOH ang mga tubag ngadto sa mga pasilidad. Kung dili nimo dawaton ang location prompt, ipasa gihapon ang imong mga tubag nga walay coordinates.',
  },
  matrix: {
    statementHeader: 'Pamahayag',
  },
  sync: {
    heading: 'Sync',
    none: 'Wala pay napasa.',
    viewQueue: 'Tan-awa ang mga nagpaabot nga pagpasa',
    runButton: 'Mag-sync karon',
    runningButton: 'Nag-sync…',
    syncedSummary: 'Na-sync ang {{count}}',
    retryingSummary: 'Gisulayan pag-usab ang {{count}}',
    rejectedSummary: '{{count}} ang gibalibaran',
    nothingToSync: 'Walay i-sync',
    submittedAt: 'gipasa {{at}}',
    retryAt: 'sulayan pag-usab sa {{at}}',
    pendingBadge: '{{count}} ang nagpaabot',
    statusPending: 'Nagpaabot',
    statusSyncing: 'Nag-sync',
    statusRetryScheduled: 'Naka-iskedyul ang pagsulay pag-usab',
    statusRejected: 'Gibalibaran',
    statusSynced: 'Na-sync',
    syncFailedFallback: 'Napakyas ang pag-sync',
  },
  crossField: {
    tenureImplausible: 'Ang gireport nga tenure ({{years}} ka tuig) dili katuohan alang sa edad nga {{age}}.',
    tenureZero: 'Years and months of service cannot both be zero. Enter at least 1 month of tenure at this facility.',
    specialtyMismatch:
      'Ang tahas nga "{{role}}" kasagaran walay medikal nga espesyalidad ({{specialty}}).',
    employmentClassDerived: 'Gisubay nga klase sa trabaho: {{employmentClass}}.',
    workloadExceeds80:
      'Ang gireport nga workload ({{days}} ka adlaw × {{hours}} ka oras = {{total}} ka oras/semana) milapas sa 80.',
    sectionGRoleMismatch:
      'Ang Seksyon G alang lamang sa mga doktor ug dentista; ang mga tubag gikan sa "{{role}}" tangtangon sa server.',
    sectionsCDRoleMismatch:
      'Ang Seksyon C ug D alang lamang sa mga tahas sa klinikal nga pag-atiman; ang mga tubag gikan sa "{{role}}" tangtangon sa server.',
  },
} as const;
