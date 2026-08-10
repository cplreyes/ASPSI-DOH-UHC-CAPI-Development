# DRAFT — csprousers.org forum post (Carl to review + post)

**Title:** CSEntry (Android): resuming a partial save raises "Out of range" on Check Box fields with 2+ ticks

**Body:**

We're running a CAPI survey (CSPro 8.0.1 authoring; tablets on the Play-Store CSEntry) and hit the following on Android:

1. A tick-all question is set up per the docs: alpha item (length = N×2), value set with one 2-char code per option, capture type **Check Box**.
2. During entry, ticking multiple options works normally (stored packed, e.g. `0102`).
3. The interviewer **partial-saves** past that question, closes the case, reopens it, and answers *yes* to advancing to the last position.
4. While CSEntry walks back to the last position, it raises **"WARNING: Out of range! Please enter a valid value for <field>"** at the multi-ticked Check Box field, and the answer must be re-entered. Fields with a single tick resume fine — only packed multi-code values trip it.

It looks like the resume walk re-validates the stored value against the value set as a plain alpha (where `0102` is of course not an entry), instead of applying the Check Box capture's multi-code semantics the way normal entry does. The old "Validate alpha fields" option that had this documented incompatibility with Check Boxes (forum topic 2831) no longer appears in CSPro 8's data-entry options, so there's nothing to untick on our side.

Screen recording of the behavior available. Is this a known issue in the current Android build, and is there an application-side workaround short of telling enumerators to re-tick after every resume?

— fill in: exact CSEntry version from the affected tablet (Settings → Apps → CSEntry) before posting.
