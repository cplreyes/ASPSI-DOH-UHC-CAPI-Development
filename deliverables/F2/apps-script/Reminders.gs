/**
 * F2 Reminders — daily Day 1/2/3 nudge for non-completers.
 *
 * Reads the FacilityMasterList Sheet (one row per HCW with their prefilled
 * link and email) and the F2-Responses Sheet. For each HCW whose link was
 * generated N days ago but who has not submitted, sends a reminder email.
 *
 * Installed as a daily 09:00 Manila trigger by buildForm().
 */

var REMINDER_BODY = {
  1: 'Hi — this is Day 1 after your F2 Healthcare Worker Survey link was sent. ' +
     'If you have already started, you can resume; your answers are saved. Link: ',
  2: 'Gentle reminder — Day 2 of your F2 survey window. The window closes after 3 days. ' +
     'Please take ~25 minutes to complete it. Link: ',
  3: 'Final reminder — today is the last day of your F2 survey window. ' +
     'Your facility\u2019s response is important for the ASPSI-DOH UHC Survey 2. Link: '
};

function runRemindersNow() {
  var props = PropertiesService.getScriptProperties();
  var sheetId = props.getProperty(PROPS_KEY_SHEET_ID);
  if (!sheetId) { Logger.log('No response sheet yet.'); return; }
  var responseSheet = SpreadsheetApp.openById(sheetId).getSheets()[0];
  var submitted = collectSubmittedEmails_(responseSheet);

  var links = getLinksSheet_();
  if (!links) { Logger.log('No F2-Links sheet yet — run generateLinks() first.'); return; }
  var data = links.getRange(2, 1, links.getLastRow() - 1, links.getLastColumn()).getValues();
  var header = links.getRange(1, 1, 1, links.getLastColumn()).getValues()[0];
  var col = function (name) { return header.indexOf(name); };

  var now = new Date();
  var sent = 0;
  data.forEach(function (row) {
    var email = row[col('hcw_email')];
    if (!email || submitted[email]) return;
    var generatedAt = new Date(row[col('link_generated_at')]);
    var daysSince = Math.floor((now - generatedAt) / (1000 * 60 * 60 * 24));
    if (daysSince < 1 || daysSince > 3) return;
    var url = row[col('prefilled_url')];
    MailApp.sendEmail({
      to: email,
      subject: 'F2 Healthcare Worker Survey — Day ' + daysSince + ' reminder',
      body: REMINDER_BODY[daysSince] + url
    });
    sent++;
  });
  Logger.log('Reminders sent: ' + sent);
}

function collectSubmittedEmails_(sheet) {
  var last = sheet.getLastRow();
  if (last < 2) return {};
  var header = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  var emailCol = -1;
  for (var i = 0; i < header.length; i++) {
    if (/email/i.test(header[i])) { emailCol = i; break; }
  }
  if (emailCol === -1) return {};
  var emails = sheet.getRange(2, emailCol + 1, last - 1, 1).getValues();
  var out = {};
  emails.forEach(function (e) { if (e[0]) out[e[0]] = true; });
  return out;
}

function getLinksSheet_() {
  var files = DriveApp.getFilesByName('F2-Links');
  if (!files.hasNext()) return null;
  return SpreadsheetApp.open(files.next()).getSheets()[0];
}
