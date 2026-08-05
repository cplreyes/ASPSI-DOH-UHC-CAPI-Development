// Cebuano bundle — app chrome DRAFT (machine-assisted, pending ASPSI QC). Survey content is NOT here; it lives in spec/translations/ceb.json.
import type { EnBundle } from './en';

export const ceb: EnBundle = {
  chrome: {
    appTitle: 'UHC Survey Y2 — Kwestyonaryo sa Survey alang sa Trabahante sa Panglawas',
    install: 'I-install',
    loading: 'Nagkarga…',
    formView: 'Porma',
    syncView: 'Sync',
    thankYouHeading: 'Salamat',
    thankYouBody: 'Ang imong tubag natipigan na niini nga device ug mo-sync kini kung naa nay koneksyon ang app.',
    // Sync-on-submit delivery gate (design F2-Facility-Slug-Links-2026-07-16) —
    // English until the ASPSI translation pass delivers dialect wording.
    delivering: 'Submitting…',
    deliveredBody: 'Submitted ✓ — your response is in. You can close this page.',
    deliveryOffline: 'Saved on this phone — it will send automatically when you are back online.',
    deliveryFailed:
      'Your response is saved on this device but could not be sent automatically. Please show this screen to ASPSI staff.',
    startNewSurvey: 'Pagsugod og bag-ong survey',
    submitFailedHeading: 'Napakyas ang pag-submit',
    submitFailedBody:
      'Wala matipigi ang imong tubag. I-tap ang retry aron mosulay pag-usab. Kung magpadayon ang problema, ang imong draft naa pa sa miaging screen.',
    submitFailedRetry: 'Sulayi pag-usab',
    submitBlockedKillSwitch:
      'Temporaryong gipahunong sa administrador ang mga pag-submit. Ang imong progreso natipigan dinhi sa device ug mo-sync kini kung magpadayon na ang pag-submit.',
    submitBlockedSpecDrift: 'Adunay gikinahanglan nga update sa app. Palihug i-reload una mosubmit.',
    killSwitchTitle: 'Temporaryong gipahunong ang mga pag-submit',
    killSwitchBody:
      'Gipahunong sa administrador ang mga pag-submit. Ang imong progreso natipigan dinhi sa device ug mo-sync kini kung magpadayon na ang pag-submit.',
    specDriftTitle: 'Gikinahanglan ang update',
    specDriftBody:
      'Ang bersyon sa imong porma ({{localVersion}}) mas daan kaysa gikinahanglan sa server ({{serverMin}}). I-reload aron makuha ang pinakabag-o.',
    reload: 'I-reload',
  },
  language: {
    label: 'Pinulongan',
    en: 'English',
    fil: 'Filipino',
  },
  enrollment: {
    heading: 'Pagpalista',
    helper:
      'Isulod ang imong HCW ID ug pilia ang imong pasilidad. Mausab nimo kini unya gikan sa Sync page.',
    hcwIdLabel: 'HCW ID',
    facilityLabel: 'Pasilidad',
    facilityPlaceholder: 'Pagpili og pasilidad…',
    noFacilitiesCached: 'Walay na-cache nga pasilidad. I-tap ang Refresh aron ma-download ang master list.',
    enrollButton: 'Pagpalista',
    refreshButton: 'I-refresh ang listahan sa pasilidad',
    refreshingButton: 'Nag-refresh…',
    changeButton: 'Usba ang pagpalista',
    changeConfirm: 'Mo-sign out niini nga device? Makapalista ka pag-usab human niini.',
    changeConfirmWithDraft:
      'Aduna kay wala mahuman nga draft. Kung usbon nimo ang pagpalista, mawala kini. Magpadayon?',
    tokenStep: 'Lakang 1: Token sa tablet',
    tokenHelper:
      'I-paste ang token gikan sa imong ASPSI ops contact. Ila kining gihimo alang niini nga tablet atol sa provisioning.',
    tokenLabel: 'Token sa tablet',
    tokenPlaceholder: 'eyJhbGc...',
    verifyTokenButton: 'I-verify ang token',
    verifyingTokenButton: 'Nag-verify…',
    tokenInvalid: 'Sayop ang pagkahimo sa token. Kontaka ang ASPSI ops alang sa bag-o.',
    tokenRevoked: 'Gibawi na kini nga tablet. Kontaka ang ASPSI ops.',
    tokenOffline: 'Wala kay koneksyon. Susiha ang imong koneksyon ug sulayi pag-usab.',
    identityStep: 'Lakang 2: Pagpaila sa imong kaugalingon',
    tokenAccepted: 'Gidawat ang token alang sa pasilidad nga {{facility}}. Pilia ang imong kaugalingon gikan sa roster sa ubos.',
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
    previous: 'Miaging',
    next: 'Sunod',
    submit: 'I-submit',
    saveDraft: 'I-save ang Draft',
    draftSaved: 'Natipigan ang draft',
    sectionLocked: 'Kompletoha ang mga seksyon sumala sa han-ay — humana usa ang kasamtangang seksyon.',
  },
  progressBar: {
    sectionLabel: 'Seksyon {{current}} sa {{total}}',
  },
  question: {
    requiredFallback: 'Kinahanglan kini nga field.',
    pleaseSpecifyLabel: 'Palihug ipasabot',
    pleaseSpecifyError: 'Palihug ipasabot',
    selectAllThatApply: 'Pilia ang tanan nga angay.',
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
    crossFieldRegion: 'Mga pasidaan sa cross-field',
    sectionHeading: 'Seksyon {{id}} — {{title}}',
    edit: 'Usba',
    submit: 'I-submit',
    // English draft pending ASPSI QC (R3 #305 hard-block message).
    blockingError: 'Please resolve the highlighted issue above before submitting.',
  },
  // #838 — tool-usability feedback (pretest). English pending ASPSI translation;
  // wording is ASPSI's call, so it is NOT localized here.
  feedback: {
    heading: 'Before you submit',
    note: 'This is about the survey tool itself, not your answers. It helps us improve it.',
    easeQuestion: 'Did you find the survey tool easy to use and navigate?',
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
    infoStudy:
      'The Asian Social Project Services, Inc. (ASPSI) invites you to participate in a study on Universal Health Care (UHC). This study aims to generate evidence on the overall experience of healthcare service providers and the general public to support continuous monitoring, evaluation, and learning of the implementation of the UHC Act, its Implementing Rules and Regulations (IRR), and packages of programs like the Yaman ng Kalusugan Program (YAKAP), No Balance Billing (NBB), Zero Balance Billing (ZBB), Bagong Urgent Care and Ambulatory Services (BUCAS) centers, and Guaranteed and Accessible Medications for Outpatient Treatment (GAMOT). The Department of Health funded this study. Your progress is saved automatically on this device — you can pause and continue at any time before submitting.',
    infoPrivacy:
      'We are committed to protecting your privacy. If you choose to participate, we will never share your information outside of the study team. We will never include your name in information shared with the government or in any reports. Your name will be kept separately from your answers in a private, secure location. For this survey, we also ask that you respect the privacy of your colleagues and patients and do not share anything you discuss here. With all research, there is a small chance that someone else might get to see your data. We try our best to prevent that, but if it happens, we will tell you as soon as possible.',
    infoBenefits:
      "Aside from this, there are no other risks to you if you take part in this study. As a benefit of the research, the knowledge gained may help the government and DOH better support your healthcare needs. Participating in this survey will also enter you into a raffle, giving you a chance to win PhP 1,000 as a way of thanking you for the time you have shared with us.",
    infoRights:
      'You are free to decline participation or to stop at any time before submitting the form. Choosing not to participate will not result in any penalty, and you will not have to pay anything to take part in this study.',
    contactsHeading:
      'If you have concerns or questions about your rights as a participant, you can contact:',
    contactsBody:
      'Single Joint Research Ethics Board (SJREB) at the Philippines Department of Health\nEmail: sjreb.doh@gmail.com\nNational Tel: (02) 651-7800 local 1328\nTel: +63 936 992 5513\n\nDepartment of Health\nName: Lindsley Jeremiah D. Villarante\nEmail: ldvillarante@doh.gov.ph\nTel: +63 (02) 8651-7800 local 1432\n\nAsian Social Project Services, Inc.\nName: Paulyn Jean A. Claro\nEmail: aspsiglobal@gmail.com\nTel: +63 917 819 6884',
    confirmHeading: 'Consent confirmation',
    confirmPrompt:
      'Please confirm whether you have read and understood the information above and whether you agree to participate in this survey. You must confirm to proceed.',
    agreeOption:
      'I have read and understood the information above. I voluntarily agree to participate in this survey.',
    declineOption: 'I do not wish to participate.',
    continueButton: 'Continue',
    declinedHeading: 'Thank you for your time',
    declinedBody:
      'You chose not to participate in this survey. No survey questions will be shown and no response has been recorded on this device. If this was a mistake, you can start over below.',
    startOver: 'Start over',
    gps_disclosure:
      'Kung mo-submit ka, marekord ang lokasyon sa imong device aron ma-map sa DOH ang mga tubag sa mga pasilidad. Kung dili nimo dawaton ang location prompt, ma-submit gihapon ang imong mga tubag nga walay coordinates.',
  },
  matrix: {
    statementHeader: 'Pamahayag',
  },
  sync: {
    heading: 'Sync',
    none: 'Wala pay mga pag-submit.',
    viewQueue: 'Tan-awa ang naghulat nga mga pag-submit',
    runButton: 'I-sync karon',
    runningButton: 'Nag-sync…',
    syncedSummary: 'Na-sync {{count}}',
    retryingSummary: 'Gisulayan pag-usab {{count}}',
    rejectedSummary: '{{count}} gibalibaran',
    nothingToSync: 'Walay i-sync',
    submittedAt: 'gisubmit {{at}}',
    retryAt: 'sulayan pag-usab sa {{at}}',
    pendingBadge: '{{count}} naghulat',
    statusPending: 'Naghulat',
    statusSyncing: 'Nag-sync',
    statusRetryScheduled: 'Naka-iskedyul ang pagsulay pag-usab',
    statusRejected: 'Gibalibaran',
    statusSynced: 'Na-sync',
    syncFailedFallback: 'Napakyas ang sync',
  },
  crossField: {
    tenureImplausible: 'Ang gireport nga tenure ({{years}} ka tuig) dili katuohan alang sa edad nga {{age}}.',
    tenureZero: 'Years and months of service cannot both be zero. Enter at least 1 month of tenure at this facility.',
    specialtyMismatch:
      'Ang papel nga "{{role}}" kasagaran walay medikal nga espesyalidad ({{specialty}}).',
    employmentClassDerived: 'Nakuha nga klase sa empleyo: {{employmentClass}}.',
    workloadExceeds80:
      'Ang gireport nga trabaho ({{days}} ka adlaw × {{hours}} ka oras = {{total}} ka oras/semana) milapas sa 80.',
    sectionGRoleMismatch:
      'Ang Seksyon G para lang sa mga doktor ug dentista; ang mga tubag gikan sa "{{role}}" ipanghimakak sa server.',
    sectionsCDRoleMismatch:
      'Ang mga Seksyon C ug D para lang sa mga papel sa klinikal nga pag-atiman; ang mga tubag gikan sa "{{role}}" ipanghimakak sa server.',
  },
};
