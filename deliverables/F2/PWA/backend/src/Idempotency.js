function findExistingSubmission(reader, clientSubmissionId) {
  if (!clientSubmissionId) return null;
  var cells = reader.readClientIdsColumn();
  if (!cells || cells.length === 0) return null;
  var offset = reader.headerRowOffset();
  for (var i = 0; i < cells.length; i++) {
    var value = cells[i][0];
    if (value && value === clientSubmissionId) {
      var rowNumber = i + 1 + offset;
      var row = reader.readRowByNumber(rowNumber);
      if (row) {
        return { submission_id: row.submission_id, row_number: rowNumber };
      }
    }
  }
  return null;
}

if (typeof module !== 'undefined') {
  module.exports = { findExistingSubmission: findExistingSubmission };
}
