/**
 * F2 Healthcare Worker Survey — Apps Script generator
 *
 * Source of truth:
 *   deliverables/F2/F2-Spec.md        — questionnaire body
 *   deliverables/F2/F2-Skip-Logic.md  — section graph
 *   deliverables/F2/F2-Validation.md  — per-field rules
 *   deliverables/F2/F2-Cross-Field.md — POST rules
 *
 * Entry points:
 *   buildForm()              — create a fresh Form + response Sheet + triggers
 *   rebuildForm()            — delete existing Form/Sheet and re-run buildForm()
 *   buildStaffEncoderForm()  — parallel Form with response_source=staff_encoded
 *   generateLinks()          — prefilled per-facility URLs from FacilityMasterList
 *   runRemindersNow()        — manual reminder dispatch
 */

var FORM_TITLE = 'F2 — Healthcare Worker Survey (UHC Survey 2)';
var FORM_TITLE_STAFF = 'F2 — Healthcare Worker Survey (staff-encoder variant)';
var RESPONSE_SHEET_TITLE = 'F2-Responses';
var PROPS_KEY_FORM_ID = 'f2_form_id';
var PROPS_KEY_SHEET_ID = 'f2_sheet_id';
var PROPS_KEY_STAFF_FORM_ID = 'f2_staff_form_id';
var REMINDER_HOUR = 9; // 09:00 Manila
var WINDOW_DAYS = 3;   // self-admin window per project_f2_self_admin_window memory

function buildForm() {
  var props = PropertiesService.getScriptProperties();
  var form = FormApp.create(FORM_TITLE);
  form.setDescription('Kindly answer this Healthcare Worker Survey for the UHC Survey 2. ' +
                      'Your responses are confidential. Estimated time: ~25 minutes. ' +
                      'You may resume within 3 days of first opening this link.');
  form.setCollectEmail(true);
  form.setRequireLogin(true);
  form.setProgressBar(true);
  form.setAllowResponseEdits(true);    // save/resume within window
  form.setLimitOneResponsePerUser(false); // staff encoder reuses form

  // Pass 1: build all page breaks (sections) so routing has targets.
  var pages = buildSectionPages_(form);

  // Pass 2: add items to each section in order, wiring routing.
  populateSections_(form, pages);

  // Attach response sheet.
  var ss = SpreadsheetApp.create(RESPONSE_SHEET_TITLE);
  form.setDestination(FormApp.DestinationType.SPREADSHEET, ss.getId());

  props.setProperty(PROPS_KEY_FORM_ID, form.getId());
  props.setProperty(PROPS_KEY_SHEET_ID, ss.getId());

  installOnSubmitTrigger_(form);
  installReminderTrigger_();

  Logger.log('Form:   ' + form.getPublishedUrl());
  Logger.log('Edit:   ' + form.getEditUrl());
  Logger.log('Sheet:  ' + ss.getUrl());
  Logger.log('FormID: ' + form.getId());
}

function rebuildForm() {
  var props = PropertiesService.getScriptProperties();
  var oldFormId = props.getProperty(PROPS_KEY_FORM_ID);
  var oldSheetId = props.getProperty(PROPS_KEY_SHEET_ID);
  if (oldFormId) { try { DriveApp.getFileById(oldFormId).setTrashed(true); } catch (e) {} }
  if (oldSheetId) { try { DriveApp.getFileById(oldSheetId).setTrashed(true); } catch (e) {} }
  clearTriggers_();
  props.deleteProperty(PROPS_KEY_FORM_ID);
  props.deleteProperty(PROPS_KEY_SHEET_ID);
  buildForm();
}

function buildStaffEncoderForm() {
  // Thin variant: build a second form that shares the same response sheet,
  // tagged response_source=staff_encoded via a hidden pre-filled field.
  var form = FormApp.create(FORM_TITLE_STAFF);
  form.setDescription('ASPSI staff encoder variant — encode paper F2 responses here. ' +
                      'Tag `response_source=staff_encoded` is set automatically.');
  form.setCollectEmail(true);
  form.setRequireLogin(true);
  form.setProgressBar(true);
  var pages = buildSectionPages_(form);
  populateSections_(form, pages, {responseSource: 'staff_encoded'});

  var props = PropertiesService.getScriptProperties();
  var sheetId = props.getProperty(PROPS_KEY_SHEET_ID);
  if (sheetId) {
    form.setDestination(FormApp.DestinationType.SPREADSHEET, sheetId);
  }
  props.setProperty(PROPS_KEY_STAFF_FORM_ID, form.getId());
  Logger.log('Staff encoder Form: ' + form.getPublishedUrl());
}

function installOnSubmitTrigger_(form) {
  // Delete any existing onFormSubmit triggers for this form, then install fresh.
  var existing = ScriptApp.getProjectTriggers();
  existing.forEach(function (t) {
    if (t.getHandlerFunction() === 'onF2FormSubmit') {
      ScriptApp.deleteTrigger(t);
    }
  });
  ScriptApp.newTrigger('onF2FormSubmit').forForm(form).onFormSubmit().create();
}

function installReminderTrigger_() {
  var existing = ScriptApp.getProjectTriggers();
  existing.forEach(function (t) {
    if (t.getHandlerFunction() === 'runRemindersNow') {
      ScriptApp.deleteTrigger(t);
    }
  });
  ScriptApp.newTrigger('runRemindersNow')
    .timeBased().atHour(REMINDER_HOUR).everyDays(1).inTimezone('Asia/Manila').create();
}

function clearTriggers_() {
  ScriptApp.getProjectTriggers().forEach(function (t) { ScriptApp.deleteTrigger(t); });
}
