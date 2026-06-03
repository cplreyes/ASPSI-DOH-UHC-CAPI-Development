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
  },
  navigator: {
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
  consent: {
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
