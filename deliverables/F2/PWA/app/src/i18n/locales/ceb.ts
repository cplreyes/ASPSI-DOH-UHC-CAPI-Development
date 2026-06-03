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
  },
  navigator: {
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
  consent: {
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
