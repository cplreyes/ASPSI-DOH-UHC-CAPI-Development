// Tagalog bundle — app chrome DRAFT (machine-assisted, pending ASPSI QC). Survey content is NOT here; it lives in spec/translations/fil.json.
import type { EnBundle } from './en';

export const fil: EnBundle = {
  chrome: {
    appTitle: 'UHC Survey Y2 — Talatanungan ng Survey para sa Manggagawang Pangkalusugan',
    install: 'I-install',
    loading: 'Naglo-load…',
    formView: 'Form',
    syncView: 'Sync',
    thankYouHeading: 'Salamat',
    thankYouBody: 'Naka-save ang iyong sagot sa device na ito at magsi-sync ito kapag online na ang app.',
    // Sync-on-submit delivery gate (design F2-Facility-Slug-Links-2026-07-16) —
    // English until the ASPSI translation pass delivers dialect wording.
    delivering: 'Submitting…',
    deliveredBody: 'Submitted ✓ — your response is in. You can close this page.',
    deliveryOffline: 'Saved on this phone — it will send automatically when you are back online.',
    deliveryFailed:
      'Your response is saved on this device but could not be sent automatically. Please show this screen to ASPSI staff.',
    startNewSurvey: 'Magsimula ng bagong survey',
    submitFailedHeading: 'Nabigo ang pagsumite',
    submitFailedBody:
      'Hindi na-save ang iyong sagot. Pindutin ang subukang muli upang mag-ulit. Kung magpatuloy ang problema, nasa nakaraang screen pa rin ang iyong draft.',
    submitFailedRetry: 'Subukang muli',
    submitBlockedKillSwitch:
      'Pansamantalang pinatigil ng administrator ang pagsumite. Naka-save nang lokal ang iyong progreso at magsi-sync ito kapag nagpatuloy na ang pagsumite.',
    submitBlockedSpecDrift: 'May kinakailangang update sa app. Pakireload muna bago magsumite.',
    killSwitchTitle: 'Pansamantalang pinatigil ang pagsumite',
    killSwitchBody:
      'Pinatigil ng administrator ang pagsumite. Naka-save nang lokal ang iyong progreso at magsi-sync ito kapag nagpatuloy na ang pagsumite.',
    specDriftTitle: 'Kinakailangan ang update',
    specDriftBody:
      'Mas luma ang bersyon ng iyong form ({{localVersion}}) kaysa sa hinihingi ng server ({{serverMin}}). I-reload upang makuha ang pinakabago.',
    reload: 'I-reload',
  },
  language: {
    label: 'Wika',
    en: 'Ingles',
    fil: 'Filipino',
  },
  enrollment: {
    heading: 'Mag-enroll',
    helper:
      'Ilagay ang iyong HCW ID at piliin ang iyong pasilidad. Maaari mong baguhin ang mga ito mamaya mula sa pahinang Sync.',
    hcwIdLabel: 'HCW ID',
    facilityLabel: 'Pasilidad',
    facilityPlaceholder: 'Pumili ng pasilidad…',
    noFacilitiesCached: 'Walang naka-cache na pasilidad. Pindutin ang Refresh upang i-download ang master list.',
    enrollButton: 'Mag-enroll',
    refreshButton: 'I-refresh ang listahan ng pasilidad',
    refreshingButton: 'Nire-refresh…',
    changeButton: 'Baguhin ang enrollment',
    changeConfirm: 'Mag-sign out sa device na ito? Maaari kang mag-enroll muli pagkatapos.',
    changeConfirmWithDraft:
      'May hindi pa natatapos na draft ka. Kapag binago ang enrollment, mabubura ito. Magpatuloy?',
    tokenStep: 'Hakbang 1: Token ng tablet',
    tokenHelper:
      'I-paste ang token mula sa iyong ASPSI ops contact. Ginawa nila ito para sa tablet na ito noong provisioning.',
    tokenLabel: 'Token ng tablet',
    tokenPlaceholder: 'eyJhbGc...',
    verifyTokenButton: 'I-verify ang token',
    verifyingTokenButton: 'Bineberipika…',
    tokenInvalid: 'May depekto ang token. Makipag-ugnayan sa ASPSI ops para sa bago.',
    tokenRevoked: 'Na-revoke na ang tablet na ito. Makipag-ugnayan sa ASPSI ops.',
    tokenOffline: 'Offline ka. Tingnan ang iyong koneksyon at subukang muli.',
    identityStep: 'Hakbang 2: Kilalanin ang iyong sarili',
    tokenAccepted: 'Tinanggap ang token para sa pasilidad na {{facility}}. Piliin ang iyong sarili sa roster sa ibaba.',
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
    previous: 'Nakaraan',
    next: 'Susunod',
    submit: 'Isumite',
    saveDraft: 'I-save ang Draft',
    draftSaved: 'Na-save ang draft',
    sectionLocked: 'Kumpletuhin ang mga seksyon ayon sa pagkakasunod — tapusin muna ang kasalukuyang seksyon.',
  },
  progressBar: {
    sectionLabel: 'Seksyon {{current}} ng {{total}}',
  },
  question: {
    requiredFallback: 'Kinakailangan ang field na ito.',
    pleaseSpecifyLabel: 'Pakitukoy',
    pleaseSpecifyError: 'Pakitukoy',
    selectAllThatApply: 'Piliin ang lahat ng naaangkop.',
    // partialDate: English draft pending ASPSI QC (R3 #306 Q35 partial-date UI).
    partialDate: {
      year: 'Year',
      month: 'Month',
      day: 'Day',
      optional: 'Optional',
    },
  },
  review: {
    heading: 'Suriin ang iyong mga sagot',
    crossFieldRegion: 'Mga babala sa pagitan ng mga field',
    sectionHeading: 'Seksyon {{id}} — {{title}}',
    edit: 'I-edit',
    submit: 'Isumite',
    // blockingError: English draft pending ASPSI QC (R3 #305 hard-block message).
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
      'Kapag nagsumite ka, itatala ang lokasyon ng iyong device upang mai-mapa ng DOH ang mga sagot sa mga pasilidad. Kung tatanggihan mo ang prompt para sa lokasyon, isusumite pa rin ang iyong mga sagot nang walang coordinates.',
  },
  matrix: {
    statementHeader: 'Pahayag',
  },
  sync: {
    heading: 'Sync',
    none: 'Wala pang mga isinumite.',
    viewQueue: 'Tingnan ang mga nakabinbing isinusumite',
    runButton: 'Mag-sync ngayon',
    runningButton: 'Nagsi-sync…',
    syncedSummary: 'Na-sync {{count}}',
    retryingSummary: 'Inuulit {{count}}',
    rejectedSummary: '{{count}} tinanggihan',
    nothingToSync: 'Walang isi-sync',
    submittedAt: 'isinumite {{at}}',
    retryAt: 'uulitin sa {{at}}',
    pendingBadge: '{{count}} nakabinbin',
    statusPending: 'Nakabinbin',
    statusSyncing: 'Nagsi-sync',
    statusRetryScheduled: 'Nakatakda ang pag-uulit',
    statusRejected: 'Tinanggihan',
    statusSynced: 'Na-sync',
    syncFailedFallback: 'Nabigo ang pag-sync',
  },
  crossField: {
    // Updated for the R3 #305 age−20 hard block; Tagalog draft pending ASPSI QC.
    tenureImplausible: 'Ang taon ng serbisyo ({{years}}) ay dapat mas mababa sa iyong edad ({{age}}) na binawasan ng 20. Pakitama ang iyong tenure o edad.',
    tenureZero: 'Years and months of service cannot both be zero. Enter at least 1 month of tenure at this facility.',
    specialtyMismatch:
      'Ang tungkuling "{{role}}" ay karaniwang walang medikal na specialty ({{specialty}}).',
    employmentClassDerived: 'Hinangong klase ng empleyo: {{employmentClass}}.',
    workloadExceeds80:
      'Ang naiulat na workload ({{days}} araw × {{hours}} oras = {{total}} oras/linggo) ay lumampas sa 80.',
    sectionGRoleMismatch:
      'Ang Seksyon G ay para lamang sa mga manggagamot at dentista; ang mga sagot mula sa "{{role}}" ay aalisin sa server.',
    sectionsCDRoleMismatch:
      'Ang Seksyon C at D ay para lamang sa mga tungkuling pang-klinikal na pangangalaga; ang mga sagot mula sa "{{role}}" ay aalisin sa server.',
  },
} as const;
