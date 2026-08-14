#!/usr/bin/env python3
r"""Structural gate for a proposed question-stem translation.

WHY THIS EXISTS
---------------
The cleared June-5 PDFs are a sound REFERENCE but a poor bulk SOURCE: the text layer runs
English and translation together in one cell, and the page breaks cut notes mid-sentence.
A 2026-08-14 adversarial audit of 1,680 proposed repairs rejected 850 of the 1,245 stem
fills - not for style, but because they carried a second question, a section heading, a
roster column header, an uncut directive, or English debris.

Chasing those one regex at a time is a losing game, because the extraction will keep
producing new variants. So the posture here is PRECISION OVER RECALL: a stem ships only if
it passes every structural check below. Anything that cannot be proven clean is left on
English fallback, which is the documented behaviour for a missing translation and is always
safe. A smaller, provably-correct set beats a large, plausible one.

Each check names the failure mode the audit actually found, so a future reader can tell
whether a rejection is real or the rule has drifted.
"""
import re

CAPWORD = re.compile(r"^[A-Z][A-Z'’/\-\.,:;()]*$")

DIRECTIVE_OPENERS = {
    "READ", "DO", "SELECT", "ASK", "PROBE", "SHOW", "NOTE", "ENUMERATOR", "INTERVIEWER",
    "RESPONDENT",
    "PLEASE", "LIST", "WRITE", "RECORD", "INDICATE",
    "BASAHON", "BASAHAON", "BASAHIN", "BASAHA", "BASAEN", "BASAHUN",
    "DAI", "DAE", "PILION", "PLION", "PILIION",
    "HUWAG", "PILIIN", "AYAW", "PILIA", "PILIEN", "SAAN", "PILII", "PUMILI",
    # heads of conditional directives ("KUNG ANG RESPONDENT NAGHATAG OG RESIBO...").
    # "NO" is deliberately NOT here: it is an ordinary word in several of these languages
    # and as an opener it fired on real content, inflating the trim set from 5 to 18.
    "KUNG", "KON", "KUN",
}

# Answer codes dragged into the stem: "0-No 1-Yes 2Respondent refused to present card".
# Worse than noise - the F4 Hiligaynon copy has the codes mis-assigned (1 = refused).
ANSWER_CODES = re.compile(r"\b\d\s*-\s*[A-Za-zÀ-ɏ]")

# A bracketed enumerator instruction: "[Saludsodem laeng no napanda iti DOH-retained
# hospital]" = "[Ask only if ...]". Square brackets, so the <...> rule never saw them.
BRACKET_NOTE = re.compile(r"\[[^\]]{10,}\]")

# A label starting with a question number is not necessarily that question's STEM - its
# sub-fields inherit the number. Case-insensitive: the dictionaries use "Other (specify)",
# "Other (Specify)" and bare "specify text".
SUBFIELD = re.compile(
    r"(—|--"
    r"|\bother\s*\(?\s*specify"
    r"|\bspecify\b"
    r"|\btext\b"
    r"|\bamount\b"
    r"|\bauto-?(computed|filled)"
    r"|\[do not ask\]"
    r"|\btotal value\b"
    r"|\bPHP\b"
    r"|\bper line\b|\bline item\b"
    r"|\bmonth\b|\byear\b|\bhours?\b|\bminutes?\b"
    r"|\bin pesos\b"
    r")",
    re.I,
)

# Not every directive is ALL CAPS. F4 Q71 carries "Enumerator: Applicable only to
# respondents in areas with GAMOT facilities" and F1 Q65 an English definition sentence,
# both in ordinary case, so the caps-run detector never sees them.
DIRECTIVE_PHRASE = re.compile(
    r"(read options|do not read|read out loud|select all that apply|select one answer"
    r"|enumerator\s*:|interviewer\s*:|applicable only|these are the requirements"
    r"|do not ask|proceed to q|if more than one|ask if answer|only for those who"
    r"|to be asked only|question relevant|if respondent|enumerator instruction"
    # ...and the same instructions written in ordinary case in the local languages, which
    # the caps-run detector cannot see: Cebuano Q103 kept "Pilia ang tanan nga mo apply."
    r"|pilia ang tanan|pilii ang tanan|piliin ang lahat|pilion an|pilien amin"
    r"|basahon an|basahin ang|basaha ang|basaen ti|ayaw basaha|huwag basahin"
    r"|saan a basaen|dai pagbasahon|dae pagbasahon)",
    re.I,
)

# An answer row dragged into the stem: "... ang bill? 1) Salary/income Sweldo/kita".
ANSWER_ROW = re.compile(r"\b\d{1,2}\s*[\)\.]\s+[A-Za-zÀ-ɏ]")

# What kind of question is being asked. A cleared entry that asks "how much" cannot be the
# translation of an instrument question that asks "which of the following" - that is the
# F3 Q107 numbering drift, where the paper's item 107 is an amount question and the
# instrument's Q107 is a payment-source multi-select. They share vocabulary (total, bill,
# confinement) so a word-overlap test passes them; the interrogative does not.
INTERROGATIVES = [
    ("how_much", re.compile(r"\bhow much\b", re.I)),
    ("how_many", re.compile(r"\bhow many\b|\bhow long\b|\bhow often\b", re.I)),
    ("which", re.compile(r"\bwhich (of the )?\b", re.I)),
    ("what", re.compile(r"\bwhat\b", re.I)),
    ("why", re.compile(r"\bwhy\b", re.I)),
    ("who", re.compile(r"\bwho\b", re.I)),
    ("where", re.compile(r"\bwhere\b", re.I)),
    ("when", re.compile(r"\bwhen\b", re.I)),
]


def interrogative(s):
    for name, rx in INTERROGATIVES:
        if rx.search(s or ""):
            return name
    return None

# Words that mark a leading fragment as ENGLISH rather than a Philippine-language stem.
# Used when the cleared English side is missing, which is exactly when the other guards
# go quiet. None of these are ordinary words in fil/bcl/bis/ceb/war/hil/ilo.
ENGLISH_LEAD = {
    "with", "the", "following", "policy", "and", "of", "for", "this", "that", "these",
    "those", "billing", "other", "what", "why", "how", "which", "are", "was", "were",
    "your", "their", "have", "has", "been", "from", "about", "would", "will",
}

# Cross-references to another question: "<...in Q65>", "sa Q121", "proceed to Q101".
FOREIGN_Q = re.compile(r"\bQ\s?\d{1,3}(\.\d)?\b", re.I)
# A questionnaire section heading dragged in with the stem: "N. Anxiety about ...".
SECTION_HEAD = re.compile(r"(^|\s)[A-Z]\.\s+[A-Z]")


def norm(s):
    return re.sub(r"\s+", " ", (s or "").strip())


def loose(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def is_caps(w):
    core = w.strip("“”\"'()[]")
    return bool(CAPWORD.match(core)) and len(re.sub(r"[^A-Z]", "", core)) >= 2


def directive_at(s):
    """-> word index where an enumerator directive starts, or None.

    Scans for the OPENER directly rather than requiring the caps run to begin with one.
    The earlier version only tested the first word of a caps run, so an acronym sitting
    immediately in front of the directive hid it:

        "... ng zero balance billing (ZBB) READ OPTIONS OUT LOUD, SELECT ALL THAT APPLY"

    started its run at "(ZBB)" - a caps word but not an opener - and the whole directive
    went undetected. Requiring three consecutive caps words FROM the opener keeps acronym
    lists ("MAIFIP, DSWD, PCSO") from matching, which is the destructive false positive.
    """
    words = s.split()
    n = len(words)
    for i, w in enumerate(words):
        core = w.strip("“”\"'()[]").strip(".,;:()")
        if core not in DIRECTIVE_OPENERS:
            continue
        if i + 3 <= n and all(is_caps(words[j]) for j in range(i, i + 3)):
            return i
    return None


def strip_paren_debris(s):
    """Remove the empty parenthesis left behind when a note is cut out.

    The Ilocano cells wrap their translation in parentheses and put the routing note
    inside them, so cutting the note strips the closing bracket and leaves the stem ending
    on "(" or "( )" - about twenty F1 Ilocano stems came back that way. The bracket is pure
    cell debris; deleting it removes nothing a respondent should read.
    """
    s = norm(s)
    for _ in range(4):
        new = re.sub(r"[\s,;:]*\(\s*\)\s*$", "", s)
        new = re.sub(r"[\s,;:]*\(\s*$", "", new)
        new = norm(new)
        if new == s:
            break
        s = new
    return s


def parens_balanced(s):
    depth = 0
    for ch in s:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth < 0:
                return False
    return depth == 0


def strip_number(label):
    return re.sub(r"^\s*\d{1,3}(\.\d)?\s*[.)]\s*", "", label or "").strip()


def token_overlap(a, b):
    """Fraction of a's content words that also appear in b."""
    wa = {w for w in re.findall(r"[a-z]{4,}", (a or "").lower())}
    wb = {w for w in re.findall(r"[a-z]{4,}", (b or "").lower())}
    if not wa:
        return 1.0
    return len(wa & wb) / len(wa)


def validate(english_label, proposed, cleared_en, qnum, prev_locale_blank=False):
    """-> (ok, reason). `reason` names the audit failure mode when rejecting."""
    p = norm(proposed)
    if not p:
        return False, "empty"

    # When the PREVIOUS question's cell is blank in this locale but this one is not, the
    # PDF's rows have shifted up and this entry is really the neighbour's text. F4 Q143
    # came back with Q142's question for exactly this reason.
    if prev_locale_blank:
        return False, "previous question is blank in this locale - the PDF rows shifted"

    if not parens_balanced(p):
        return False, "unbalanced parentheses - a bracketed span was cut in half"

    if ANSWER_CODES.search(p):
        return False, "answer codes glued into the stem (e.g. '0-No 1-Yes')"

    if BRACKET_NOTE.search(p):
        return False, "carries a bracketed enumerator instruction"

    if SUBFIELD.search(english_label or ""):
        return False, "target is a sub-field of the question, not its stem"

    if directive_at(p) is not None:
        return False, "an enumerator directive survives in the value (would double-print)"

    m = DIRECTIVE_PHRASE.search(p)
    if m:
        return False, f"carries an instruction in ordinary case ({m.group(0)!r})"

    # A directive the page break cut off mid-phrase leaves a stub too short for the
    # three-word rule: Ilocano Q50 ends "... iti lokal a lugaryo? SAAN A", the head of
    # "SAAN A BASAEN TI OPTIONS".
    tail = p.split()[-3:]
    if any(w.strip("“”\"'()[].,;:") in DIRECTIVE_OPENERS for w in tail):
        return False, "ends on a truncated directive"

    # A label that is a field DESCRIPTION rather than a question ("Income category
    # corresponding to the respondent's approximate monthly income") belongs to a derived
    # or coded item, not to the question the cleared entry answers. Writing the question
    # onto it relabels a coded field with someone else's text.
    en_body_q = strip_number(english_label)
    if "?" not in en_body_q and "?" in p:
        return False, "label is a derived/coded field, not the question itself"

    # Without the cleared ENGLISH stem there is nothing to check the binding or the length
    # against, and those guards would silently pass. That blind spot is what let the
    # Cebuano "with the following?" debris and the F3 Q18 mis-binding through, so a missing
    # English side is now a rejection rather than a free pass.
    if not norm(cleared_en):
        return False, "no cleared English stem to validate against"

    if "<" in p or ">" in p:
        return False, "carries a questionnaire routing annotation"

    # A reference to another question means the extraction crossed a boundary.
    others = [m.group(0) for m in FOREIGN_Q.finditer(p)]
    if others:
        return False, f"refers to another question ({others[0]}) - crossed a boundary"

    # A trailing parenthetical ending in a bare question number is a routing note with the
    # "Q" lost in extraction: Ilocano Q114 came back with
    # "(No saan a na-availed ti PhilHealth iti 113)" = "(If PhilHealth was not availed in 113)".
    m = re.search(r"\([^)]{8,}\b\d{1,3}\s*\)\s*$", p)
    if m:
        return False, "ends in a routing note referring to another question number"

    if SECTION_HEAD.search(p):
        return False, "carries a section heading"

    if p.count("?") >= 3:
        return False, "three or more question marks - looks like several questions merged"

    en_body = strip_number(english_label)
    if loose(p) == loose(en_body):
        return False, "identical to the English - a no-op that hides a real gap"

    # Length sanity against the cleared ENGLISH stem catches both blobs and truncations.
    base = norm(cleared_en) or en_body
    if base:
        ratio = len(p) / max(len(base), 1)
        if ratio > 2.6:
            return False, f"{ratio:.1f}x longer than the English - multi-question blob"
        if ratio < 0.35:
            return False, f"{ratio:.1f}x the English length - truncated"

    if ANSWER_ROW.search(p):
        return False, "an answer row is glued onto the stem"

    # Wrong-binding guard: the map key must actually be the question the cleared entry is
    # for. If the English label and the cleared English stem barely share vocabulary, the
    # proposal belongs to a different question.
    if base and token_overlap(en_body, base) < 0.34:
        return False, "English label does not match the cleared entry - wrong question"

    # Vocabulary overlap alone is not enough when the paper and the instrument number
    # things differently: cleared 107 "How much was the total bill for your confinement?"
    # and instrument Q107 "Which of the following did you use to pay for the total bill..."
    # share most of their nouns while asking completely different things.
    a, b = interrogative(en_body), interrogative(base)
    if a and b and a != b:
        return False, f"question type differs - label asks '{a}', cleared entry asks '{b}'"

    # A short fragment sitting in front of the first question mark is the tail of the
    # PREVIOUS question's cell: Bikol Q22 came back as "household? Igwa ba an pasyente...".
    head = p.split("?")[0]
    if "?" in p and len(head.split()) <= 3 and len(p.split()) - len(head.split()) >= 5:
        return False, f"leading fragment before the first question mark ({head.strip()!r})"

    # Leading English debris. The PDF puts English and translation in one cell, so a split
    # can land mid-sentence and leave the tail of the English question in front of the
    # translation - Cebuano Q122-Q134 all begin "with the following? Nganong lisud ...",
    # and Bisaya Q140 begins 'billing" policy? Sa inyong panan-aw ...'. Repairing that
    # needs a judgement about where the translation starts, so it is REJECTED rather than
    # guessed: English fallback is always safe, a mis-cut is not.
    lead = re.split(r"[?.]", p, 1)[0]
    lw = re.findall(r"[A-Za-z]{3,}", lead)[:6]
    if lw:
        base_l = (base or "").lower()
        from_english = sum(1 for w in lw if base_l and w.lower() in base_l)
        looks_english = sum(1 for w in lw if w.lower() in ENGLISH_LEAD)
        if from_english / len(lw) >= 0.6 or looks_english / len(lw) >= 0.6:
            return False, "starts with English text carried over from the cleared English"

    first = p.split()[0]
    if first.strip(".,;:") in (")", "]", "”") or p[0] in ")]}”":
        return False, "starts on stray closing punctuation - PDF debris"
    if re.match(r"^[a-z]{1,3}\b", p) and not re.match(r"^(an|ang|ano|ti|iti|sa|ha|no|ug|og|kon|kun|nga|si|ni|mga)\b", p, re.I):
        return False, "starts mid-word or on a fragment - PDF debris"

    return True, ""


def validate_option(english_option, proposed):
    """-> (ok, reason) for a value-set OPTION label.

    Options need their own gate. The 2026-08-14 audit rejected 15 of 67 and several were
    destructive, all from the same two extraction faults:

      * the cell was empty or held punctuation, so the option would render as a bare "/"
        or "(" - "Medical Officer" became "/" in four locales;
      * index pairing picked up the NEXT option, sometimes dragging the following section
        heading with it - "Php 2,000 and above" became
        "Other (Specify) Iba pa (ispecify) Q. Anxiety about Household Finances".

    An option label is short and self-contained, so these are easy to catch on shape alone.
    """
    p = norm(proposed)
    if not p:
        return False, "empty"
    if len(re.sub(r"[^A-Za-zÀ-ɏ]", "", p)) < 2:
        return False, f"no real text ({p!r}) - PDF punctuation artifact"
    if SECTION_HEAD.search(p):
        return False, "carries a section heading - picked up the next option"
    if DIRECTIVE_PHRASE.search(p):
        return False, "carries an instruction"
    if "<" in p or ">" in p:
        return False, "carries a routing annotation"
    en = norm(english_option)
    # "(specify)" appearing only on the translated side means the neighbouring
    # Other-(Specify) row was pulled in.
    if re.search(r"\(\s*i?-?\s*specify", p, re.I) and not re.search(r"specify", en, re.I):
        return False, "picked up the neighbouring Other-(Specify) option"
    if re.search(r"amount in pesos|kantidad sa peso|halaga sa piso", p, re.I) \
            and not re.search(r"amount", en, re.I):
        return False, "carries a roster column header"
    if len(p) > 3 * max(len(en), 1) and len(p) - len(en) > 25:
        return False, f"{len(p)}ch vs {len(en)}ch English - neighbouring text glued on"

    # The English option repeated at the END with something in front means the row above
    # was pulled in: Cebuano "Barangay Health Worker" came back as
    # "LGU Barangay Health Worker", and LGU is the separate option before it.
    if en and p.lower().endswith(en.lower()) and len(p) > len(en) + 2:
        return False, f"prefixed with the preceding option ({p[:len(p) - len(en)].strip()!r})"

    # A value ending on a bare linker was cut before its noun - Ilocano "Never" came back
    # as "Pulos a", which is not a usable label.
    LINKERS = {"a", "ti", "ken", "nga", "ng", "sa", "ug", "og", "ang", "an", "kan", "ni",
               "si", "han", "hin", "iti", "ti", "no", "kag", "sang"}
    words = p.split()
    if words and words[-1].strip(".,;:").lower() in LINKERS:
        return False, f"ends on the dangling linker {words[-1]!r} - cut before its noun"

    return True, ""


def dedupe_across_questions(adds):
    """Reject a value proposed for two genuinely different questions.

    The F3 115.1/115.2 blocks are the worst case: twelve distinct checkbox labels per
    locale all received the Q115 stem. If the same text is proposed for two different
    English labels, at most one can be right, and nothing here can tell which - so both go.

    `adds` maps english_label -> proposed. Returns (kept, dropped).
    """
    by_value = {}
    for k, v in adds.items():
        by_value.setdefault(loose(v), []).append(k)
    kept, dropped = {}, {}
    for _v, keys in by_value.items():
        if len(keys) == 1:
            kept[keys[0]] = adds[keys[0]]
        else:
            for k in keys:
                dropped[k] = "same text proposed for %d different questions" % len(keys)
    return kept, dropped
