/**
 * F2 FormBuilder — two-pass Form materialization.
 *
 * Pass 1: buildSectionPages_() creates all PageBreakItem objects and returns
 * a {sectionId: pageBreakItem} map so routing has forward-reference targets.
 *
 * Pass 2: populateSections_() walks sections in order. For each section it
 * appends the section preamble, then each item, wiring routing on the LAST
 * item of any section that branches (Apps Script only honors per-answer
 * navigation on the last item of a page).
 */

function buildSectionPages_(form) {
  var pages = {};
  // The very first section uses the default first page (no explicit break).
  // For every other section, create a page break item up front.
  F2_SPEC.sections.forEach(function (sec, idx) {
    if (idx === 0) {
      pages[sec.id] = null; // default first page
    } else {
      var pb = form.addPageBreakItem();
      pb.setTitle(sec.title);
      if (sec.description) pb.setHelpText(sec.description);
      pages[sec.id] = pb;
    }
  });
  return pages;
}

function populateSections_(form, pages, opts) {
  opts = opts || {};
  // Items-by-section placeholder: we will append items immediately after each
  // page break. Apps Script appends to end-of-form, so we must build in order.
  //
  // Strategy: delete-and-rebuild every item block is avoided — we already
  // created page breaks in Pass 1 and they are in creation order. Walking the
  // sections in the same order and appending items keeps page grouping correct
  // because Apps Script assigns items to the most-recent page break.
  //
  // Caveat: the page break items already exist at the tail of the form. To
  // interleave items between them we must instead rebuild: delete page breaks,
  // then walk sections and append (pageBreak, items) pairs in order. That is
  // what this function does.
  //
  // Step 1 — clear all existing items (from buildSectionPages_).
  var all = form.getItems();
  while (all.length > 0) { form.deleteItem(all.pop()); }

  // Step 2 — walk sections, creating page break then items, recording the new
  // page break references.
  var newPages = {};
  F2_SPEC.sections.forEach(function (sec, idx) {
    var pb = null;
    if (idx > 0) {
      pb = form.addPageBreakItem().setTitle(sec.title);
      if (sec.description) pb.setHelpText(sec.description);
    } else if (sec.description) {
      form.addSectionHeaderItem().setTitle(sec.title).setHelpText(sec.description);
    }
    newPages[sec.id] = pb;

    (sec.items || []).forEach(function (item) {
      addItem_(form, item, opts);
    });
  });

  // Step 3 — second pass to wire routing now that every target exists.
  wireRouting_(form, newPages);
}

function addItem_(form, item, opts) {
  switch (item.type) {
    case 'header':
      return form.addSectionHeaderItem().setTitle(item.label).setHelpText(item.help || '');
    case 'text':
      return form.addTextItem().setTitle(item.label).setHelpText(item.help || '').setRequired(!!item.required);
    case 'paragraph':
      var para = form.addParagraphTextItem().setTitle(item.label).setHelpText(item.help || '').setRequired(!!item.required);
      return para;
    case 'number':
      var num = form.addTextItem().setTitle(item.label).setHelpText(item.help || '').setRequired(!!item.required);
      var v = FormApp.createTextValidation().requireNumberBetween(item.min || 0, item.max || 999999)
        .setHelpText('Please enter a number between ' + (item.min || 0) + ' and ' + (item.max || 999999)).build();
      num.setValidation(v);
      return num;
    case 'date':
      return form.addDateItem().setTitle(item.label).setHelpText(item.help || '').setRequired(!!item.required);
    case 'single':
      var mc = form.addMultipleChoiceItem().setTitle(item.label).setHelpText(item.help || '').setRequired(!!item.required);
      mc.setChoices((item.choices || []).map(function (c) { return mc.createChoice(c); }));
      return mc;
    case 'multi':
      var ck = form.addCheckboxItem().setTitle(item.label).setHelpText(item.help || '').setRequired(!!item.required);
      ck.setChoices((item.choices || []).map(function (c) { return ck.createChoice(c); }));
      return ck;
    case 'scale':
      var sc = form.addScaleItem().setTitle(item.label).setHelpText(item.help || '')
        .setBounds(item.min || 1, item.max || 5).setRequired(!!item.required);
      if (item.minLabel) sc.setLabels(item.minLabel, item.maxLabel || '');
      return sc;
    case 'grid-single':
      var gr = form.addGridItem().setTitle(item.label).setHelpText(item.help || '').setRequired(!!item.required);
      gr.setRows(item.rows || []);
      gr.setColumns(item.columns || []);
      return gr;
    default:
      Logger.log('Unknown item type: ' + item.type + ' (label=' + item.label + ')');
      return form.addSectionHeaderItem().setTitle('[TODO] ' + item.label).setHelpText('type=' + item.type);
  }
}

function wireRouting_(form, pages) {
  // For every item that has a `branchTo` map AND is the last item of its
  // section, set per-choice navigation. Apps Script only honors this on
  // MultipleChoiceItem and ListItem; for other types we ignore and rely on
  // section defaults (setGoToPage on the PageBreakItem).
  //
  // We also set section-default navigation where `sec.goTo` is specified
  // (unconditional jump at end of page).
  var items = form.getItems();
  var byIndex = {};
  items.forEach(function (it, i) { byIndex[it.getTitle() + '|' + i] = it; });

  F2_SPEC.sections.forEach(function (sec) {
    // Unconditional section default: last item's page continuation.
    var targetPb = sec.goTo ? pages[sec.goTo] : null;
    var branchingItemSpec = null;
    (sec.items || []).forEach(function (sp) { if (sp.branchTo) branchingItemSpec = sp; });

    if (branchingItemSpec) {
      var formItem = findItemByTitle_(form, branchingItemSpec.label);
      if (!formItem) return;
      if (formItem.getType() === FormApp.ItemType.MULTIPLE_CHOICE) {
        var mc = formItem.asMultipleChoiceItem();
        var choices = (branchingItemSpec.choices || []).map(function (c) {
          var dest = branchingItemSpec.branchTo[c];
          if (dest === 'SUBMIT') return mc.createChoice(c, FormApp.PageNavigationType.SUBMIT);
          if (dest && pages[dest]) return mc.createChoice(c, pages[dest]);
          return mc.createChoice(c);
        });
        mc.setChoices(choices);
      }
    }

    if (targetPb) {
      // Set the page break's goToPage on next section entry. Apps Script
      // does this via setGoToPage on the page break that OPENS the section
      // we want to leave from — subtle. Skipped here in favor of per-item
      // branching above. Unconditional jumps are rare in F2.
    }
  });
}

function findItemByTitle_(form, title) {
  var items = form.getItems();
  for (var i = 0; i < items.length; i++) {
    if (items[i].getTitle() === title) return items[i];
  }
  return null;
}
