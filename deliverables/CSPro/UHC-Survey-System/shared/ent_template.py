"""ent_template.py — canonical CSPro 8.0 .ent property block.

Source-of-truth: the working F1 .ent at
deliverables/CSPro/F1/FacilityHeadSurvey.ent (Carl's hand-laid Designer
output that opens cleanly in CSPro 8.0).

Use:
    from shared.ent_template import canonical_logic_settings, canonical_properties

    ENT = {
        "software": "CSPro", "version": 8.0, "fileType": "application", "type": "entry",
        "name": "...", "label": "...",
        "dictionaries": [...],
        "forms": [...],
        "questionText": [...],
        "code": [...],
        "messages": [...],
        "logicSettings": canonical_logic_settings(),
        "properties":    canonical_properties(),
        "userSettings": [...],   # spliced by env_loader at build time
    }
"""


def canonical_logic_settings() -> dict:
    return {
        "version": 2.0,
        "caseSensitive": {"symbols": False},
        "actionInvoker": {
            "accessFromExternalCaller": "promptIfNoValidAccessToken",
            "convertResultsForLogic": True,
        },
    }


def canonical_properties() -> dict:
    return {
        "askOperatorId": False,
        "autoAdvanceOnSelection": False,
        "caseTree": "mobileOnly",
        "centerForms": False,
        "createListing": False,
        "createLog": False,
        "decimalMark": "dot",
        "displayCodesAlongsideLabels": False,
        "notes": {"delete": "all", "edit": "all"},
        "partialSave": {"operatorEnabled": False},
        "showEndCaseMessage": True,
        "showOnlyDiscreteValuesInComboBoxes": True,
        "showFieldLabels": True,
        "showErrorMessageNumbers": False,
        "showQuestionText": True,
        "showRefusals": True,
        "verify": {"frequency": 1, "start": 1},
        "htmlDialogs": True,
        "paradata": {
            "collection": "all",
            "recordCoordinates": False,
            "recordInitialPropertyValues": False,
            "recordIteratorLoadCases": False,
            "recordValues": False,
            "deviceStateIntervalMinutes": 5,
        },
        "useHtmlComponentsInsteadOfNativeVersions": False,
    }
