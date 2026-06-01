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
