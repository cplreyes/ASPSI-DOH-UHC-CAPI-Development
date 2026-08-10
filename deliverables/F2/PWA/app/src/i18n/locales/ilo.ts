// Ilocano bundle — app CHROME is English-fallback (DRAFT, pending ASPSI QC).
// The Ilocano SURVEY CONTENT (questions, choices, sections) is fully wired and
// lives in spec/translations/ilo.json. App-furniture strings (buttons, sync,
// errors) are not in the ASPSI questionnaire docs, so they show English until QC.
import type { EnBundle } from './en';

export const ilo: EnBundle = {
  chrome: {
    appTitle: 'UHC Survey Y2 — Healthcare Worker Survey Questionnaire',
    install: 'Install',
    loading: 'Loading…',
    formView: 'Form',
    syncView: 'Sync',
    thankYouHeading: 'Thank you',
    thankYouBody: 'Your response is saved on this device and will sync when the app is online.',
    // Sync-on-submit delivery gate (design F2-Facility-Slug-Links-2026-07-16) —
    // English until the ASPSI translation pass delivers dialect wording.
    delivering: 'Submitting…',
    deliveredBody: 'Submitted ✓ — your response is in. You can close this page.',
    deliveryOffline: 'Saved on this phone — it will send automatically when you are back online.',
    deliveryFailed:
      'Your response is saved on this device but could not be sent automatically. Please show this screen to ASPSI staff.',
    startNewSurvey: 'Start new survey',
    submitFailedHeading: 'Submission failed',
    submitFailedBody:
      'Your response could not be saved. Tap retry to try again. If the problem persists, your draft is still on the previous screen.',
    submitFailedRetry: 'Retry',
    submitBlockedKillSwitch:
      'Submissions are temporarily paused by the administrator. Your progress is saved locally and will sync when submissions resume.',
    submitBlockedSpecDrift: 'A required app update is available. Please reload before submitting.',
    killSwitchTitle: 'Submissions temporarily paused',
    killSwitchBody:
      'The administrator has paused submissions. Your progress is saved locally and will sync when submissions resume.',
    specDriftTitle: 'Update required',
    specDriftBody:
      'Your form version ({{localVersion}}) is older than the server requires ({{serverMin}}). Reload to get the latest.',
    reload: 'Reload',
  },
  language: {
    label: 'Language',
    en: 'English',
    fil: 'Filipino',
  },
  enrollment: {
    heading: 'Enroll',
    helper:
      'Enter your HCW ID and select your facility. You can change these later from the Sync page.',
    hcwIdLabel: 'HCW ID',
    facilityLabel: 'Facility',
    facilityPlaceholder: 'Select a facility…',
    noFacilitiesCached: 'No facilities cached. Tap Refresh to download the master list.',
    enrollButton: 'Enroll',
    refreshButton: 'Refresh facility list',
    refreshingButton: 'Refreshing…',
    changeButton: 'Change enrollment',
    changeConfirm: 'Sign out of this device? You can re-enroll afterward.',
    changeConfirmWithDraft:
      'You have an unfinished draft. Changing enrollment will discard it. Continue?',
    tokenStep: 'Step 1: Tablet token',
    tokenHelper:
      'Paste the token from your ASPSI ops contact. They generated it for this tablet during provisioning.',
    tokenLabel: 'Tablet token',
    tokenPlaceholder: 'eyJhbGc...',
    verifyTokenButton: 'Verify token',
    verifyingTokenButton: 'Verifying…',
    tokenInvalid: 'Token malformed. Contact ASPSI ops for a new one.',
    tokenRevoked: 'This tablet has been revoked. Contact ASPSI ops.',
    tokenOffline: "You're offline. Check your connection and retry.",
    identityStep: 'Step 2: Identify yourself',
    tokenAccepted: 'Token accepted for facility {{facility}}. Pick yourself from the roster below.',
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
    previous: 'Previous',
    next: 'Next',
    submit: 'Submit',
    saveDraft: 'Save Draft',
    draftSaved: 'Draft saved',
    sectionLocked: 'Complete sections in order — finish the current section first.',
  },
  progressBar: {
    sectionLabel: 'Section {{current}} of {{total}}',
  },
  question: {
    requiredFallback: 'This field is required.',
    pleaseSpecifyLabel: 'Please specify',
    pleaseSpecifyError: 'Please specify',
    selectAllThatApply: 'Select all that apply.',
    partialDate: {
      year: 'Year',
      month: 'Month',
      day: 'Day',
      optional: 'Optional',
    },
  },
  review: {
    heading: 'Review your answers',
    crossFieldRegion: 'Cross-field warnings',
    sectionHeading: 'Section {{id}} — {{title}}',
    edit: 'Edit',
    submit: 'Submit',
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
      'When you submit, your device location will be recorded so DOH can map responses to facilities. If you decline the location prompt, your answers are still submitted without coordinates.',
  },
  matrix: {
    statementHeader: 'Statement',
  },
  sync: {
    heading: 'Sync',
    none: 'No submissions yet.',
    viewQueue: 'View pending submissions',
    runButton: 'Sync now',
    runningButton: 'Syncing…',
    syncedSummary: 'Synced {{count}}',
    retryingSummary: 'Retrying {{count}}',
    rejectedSummary: '{{count}} rejected',
    nothingToSync: 'Nothing to sync',
    submittedAt: 'submitted {{at}}',
    retryAt: 'retry at {{at}}',
    pendingBadge: '{{count}} pending',
    statusPending: 'Pending',
    statusSyncing: 'Syncing',
    statusRetryScheduled: 'Retry scheduled',
    statusRejected: 'Rejected',
    statusSynced: 'Synced',
    syncFailedFallback: 'Sync failed',
  },
  crossField: {
    tenureImplausible: 'Years of service ({{years}}) must be less than your age ({{age}}) minus 20. Please correct your tenure or age.',
    tenureZero: 'Years and months of service cannot both be zero. Enter at least 1 month of tenure at this facility.',
    specialtyMismatch:
      'Role "{{role}}" does not normally carry a medical specialty ({{specialty}}).',
    employmentClassDerived: 'Derived employment class: {{employmentClass}}.',
    workloadExceeds80:
      'Reported workload ({{days}} days × {{hours}} hrs = {{total}} hrs/week) exceeds 80.',
    sectionGRoleMismatch:
      'Section G is for physicians and dentists only; answers from "{{role}}" will be dropped server-side.',
    sectionsCDRoleMismatch:
      'Sections C and D are for clinical-care roles only; answers from "{{role}}" will be dropped server-side.',
  },
};
