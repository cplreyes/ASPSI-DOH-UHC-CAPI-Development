/**
 * F2 Links — prefilled URL generator from a FacilityMasterList Sheet.
 *
 * Expected columns in FacilityMasterList:
 *   facility_id, facility_name, facility_type, facility_has_bucas,
 *   facility_has_gamot, region, province, city_mun, barangay, hcw_emails
 *
 * hcw_emails is a semicolon-separated list. generateLinks() produces one row
 * per (facility × email) in a new Sheet named F2-Links with a prefilled URL
 * that bakes facility_id, facility_type, facility_has_bucas, facility_has_gamot,
 * and response_source=self into the URL.
 */

function generateLinks() {
  var props = PropertiesService.getScriptProperties();
  var formId = props.getProperty(PROPS_KEY_FORM_ID);
  if (!formId) throw new Error('Run buildForm() first.');
  var form = FormApp.openById(formId);

  var masterFiles = DriveApp.getFilesByName('FacilityMasterList');
  if (!masterFiles.hasNext()) throw new Error('FacilityMasterList Sheet not found in Drive.');
  var master = SpreadsheetApp.open(masterFiles.next()).getSheets()[0];
  var last = master.getLastRow();
  if (last < 2) throw new Error('FacilityMasterList is empty.');
  var header = master.getRange(1, 1, 1, master.getLastColumn()).getValues()[0];
  var rows = master.getRange(2, 1, last - 1, master.getLastColumn()).getValues();
  var col = function (name) { return header.indexOf(name); };

  // Cache prefill field lookups
  var items = form.getItems();
  function findItem(partial) {
    for (var i = 0; i < items.length; i++) {
      if (items[i].getTitle().indexOf(partial) !== -1) return items[i];
    }
    return null;
  }
  var facIdItem    = findItem('facility_id');
  var facTypeItem  = findItem('Please confirm your facility type');
  var bucasItem    = findItem('BUCAS Center');
  var gamotItem    = findItem('GAMOT Pharmacy');
  var sourceItem   = findItem('response_source');

  // Open/create F2-Links sheet
  var outFile = DriveApp.getFilesByName('F2-Links');
  var outSS = outFile.hasNext() ? SpreadsheetApp.open(outFile.next()) : SpreadsheetApp.create('F2-Links');
  var outSheet = outSS.getSheets()[0];
  outSheet.clear();
  outSheet.appendRow(['facility_id','facility_name','hcw_email','prefilled_url','link_generated_at']);

  var now = new Date();
  var count = 0;
  rows.forEach(function (row) {
    var facId = row[col('facility_id')];
    var facName = row[col('facility_name')];
    var facType = row[col('facility_type')];
    var hasBucas = row[col('facility_has_bucas')];
    var hasGamot = row[col('facility_has_gamot')];
    var emails = String(row[col('hcw_emails')] || '').split(';').map(function (e) { return e.trim(); }).filter(Boolean);
    emails.forEach(function (email) {
      var resp = form.createResponse();
      if (facIdItem)   resp.withItemResponse(facIdItem.asTextItem().createResponse(String(facId)));
      if (facTypeItem) resp.withItemResponse(facTypeItem.asMultipleChoiceItem().createResponse(String(facType)));
      if (bucasItem)   resp.withItemResponse(bucasItem.asMultipleChoiceItem().createResponse(String(hasBucas)));
      if (gamotItem)   resp.withItemResponse(gamotItem.asMultipleChoiceItem().createResponse(String(hasGamot)));
      if (sourceItem)  resp.withItemResponse(sourceItem.asTextItem().createResponse('self'));
      var url = resp.toPrefilledUrl();
      outSheet.appendRow([facId, facName, email, url, now]);
      count++;
    });
  });
  Logger.log('Generated ' + count + ' prefilled links into F2-Links.');
}
