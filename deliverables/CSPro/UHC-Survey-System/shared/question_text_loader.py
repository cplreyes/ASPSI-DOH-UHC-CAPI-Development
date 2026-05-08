"""question_text_loader.py — extract verbatim question text per item from spec MD.

Per memory rule (feedback_verbatim_questionnaire_labels), every item label and
[Text] block must use exact source-questionnaire wording — NEVER paraphrase.
This loader reads the canonical spec MD and indexes Q-text by item name.
"""
import re
from pathlib import Path


# Match: ### ITEM_NAME\n<one or more text lines until next ### or ## or end>
PATTERN = re.compile(
    r"^### ([A-Z][A-Z0-9_]*)\n(.+?)(?=^#{1,3} |\Z)",
    flags=re.MULTILINE | re.DOTALL,
)


def load_question_texts(md_path: Path) -> dict[str, str]:
    """Return {item_name: first-non-empty-line-of-q-text} from spec MD.

    Items not found in the MD return None when keyed via .get().
    """
    content = md_path.read_text(encoding="utf-8")
    out: dict[str, str] = {}
    for match in PATTERN.finditer(content):
        item_name = match.group(1)
        body = match.group(2).strip()
        first_line = next((line.strip() for line in body.splitlines() if line.strip()), "")
        if first_line:
            out[item_name] = first_line
    return out
