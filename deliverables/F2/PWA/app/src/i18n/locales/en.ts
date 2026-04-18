// English resource bundle for the F2 PWA.
// Mirror every key in fil.ts. New keys MUST be added to both files.
export const en = {
  chrome: {
    appTitle: 'F2 Survey',
    install: 'Install',
    loading: 'Loading…',
    formView: 'Form',
    syncView: 'Sync',
    thankYouHeading: 'Thank you',
    thankYouBody: 'Your response is saved on this device and will sync when the app is online.',
  },
  language: {
    label: 'Language',
    en: 'English',
    fil: 'Filipino',
  },
  enrollment: {
    heading: 'Enroll',
    helper: 'Enter your HCW ID and select your facility. You can change these later from the Sync page.',
    hcwIdLabel: 'HCW ID',
    facilityLabel: 'Facility',
    facilityPlaceholder: 'Select a facility…',
    noFacilitiesCached: 'No facilities cached. Tap Refresh to download the master list.',
    enrollButton: 'Enroll',
    refreshButton: 'Refresh facility list',
    refreshingButton: 'Refreshing…',
  },
  navigator: {
    previous: 'Previous',
    next: 'Next',
    submit: 'Submit',
  },
  question: {
    requiredFallback: 'This field is required.',
    pleaseSpecifyLabel: 'Please specify',
    pleaseSpecifyError: 'Please specify',
  },
  review: {
    heading: 'Review your answers',
    crossFieldRegion: 'Cross-field warnings',
    sectionHeading: 'Section {{id}} — {{title}}',
    edit: 'Edit',
    submit: 'Submit',
  },
  sync: {
    heading: 'Sync',
    none: 'No submissions yet.',
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
    tenureImplausible:
      'Reported tenure ({{years}} years) is implausible for age {{age}}.',
    specialtyMismatch:
      'Role "{{role}}" does not normally carry a medical specialty ({{specialty}}).',
    employmentClassDerived:
      'Derived employment class: {{employmentClass}}.',
    workloadExceeds80:
      'Reported workload ({{days}} days × {{hours}} hrs = {{total}} hrs/week) exceeds 80.',
    sectionGRoleMismatch:
      'Section G is for physicians and dentists only; answers from "{{role}}" will be dropped server-side.',
    sectionsCDRoleMismatch:
      'Sections C and D are for clinical-care roles only; answers from "{{role}}" will be dropped server-side.',
  },
} as const;

export type EnBundle = typeof en;
