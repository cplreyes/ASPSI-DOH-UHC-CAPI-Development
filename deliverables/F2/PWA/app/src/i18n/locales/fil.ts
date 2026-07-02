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
