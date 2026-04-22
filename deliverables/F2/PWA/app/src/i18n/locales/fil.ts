// Filipino resource bundle for the F2 PWA.
// Values are placeholder-equal-to-English until ASPSI delivers translations.
// Key shape MUST match en.ts exactly — i18next will fall back to en for any
// missing key, but a TypeScript constraint below makes drift a compile error.
import type { EnBundle } from './en';

export const fil: EnBundle = {
  chrome: {
    appTitle: 'UHC Survey Y2 — Healthcare Worker Survey Questionnaire',
    install: 'Install',
    loading: 'Loading…',
    formView: 'Form',
    syncView: 'Sync',
    thankYouHeading: 'Thank you',
    thankYouBody: 'Your response is saved on this device and will sync when the app is online.',
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
  },
  navigator: {
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
    tenureImplausible: 'Reported tenure ({{years}} years) is implausible for age {{age}}.',
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
