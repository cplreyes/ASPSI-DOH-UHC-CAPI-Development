# P5 coordinator run-sheet — 5 minutes, then the round is open

Everything else is done: guide dated (Jul 10–14), label + issue **#836** live, kickoff message
already drafted in `#f2-pwa-uat` (just hit send after step 3).

---

## Step 1 — Log in (30 s)

`https://uhc-hcw.asiansocial.org/admin` → your existing username + password.
*(`carl_admin` has `password_must_change=0`, so no forced rotation for you. `daisy_admin`,
`data_reader_test`, `data_reader_uat` will be prompted on their first login — expected.)*

## Step 2 — Create the QN-leg HCW (1 min)

Data → **HCWs** tab → **Create**:

| Field | Value |
|---|---|
| HCW ID | `p5-qn-check` |
| Facility ID | `040340002` |
| Facility name | `Laguna UAT facility (QN leg)` |

The 12-digit QN auto-assigns. **Expect `040340002001`** — leading zero intact. If you see
`40340002001` (11 digits) something regressed; stop and tell me.

## Step 3 — Reissue five tokens (3 min)

For each row: find it → amber **Reissue** → confirm → copy the **Enrollment URL**.

| # | HCW ID | Tester | Current jti (sanity check) |
|---|---|---|---|
| 1 | `DEMO-HCW-004` | Shan | `95104c8b…` |
| 2 | `DEMO-HCW-007` | Kidd | `22497e26…` |
| 3 | `DEMO-HCW-002` | Marriz | `84e01cb4…` |
| 4 | `DEMO-HCW-005` | Aly | `81148171…` |
| 5 | `p5-qn-check` | QN volunteer | *(fresh from step 2)* |

Each success screen gives a QR, the URL, the raw token, and a 30-day expiry.
"Token already reissued by another admin" = someone else touched the row; refresh and redo.

## Step 4 — Post credentials, then send the kickoff

Paste into `#f2-pwa-uat` as a **code block** (Slack eats markdown tables), then **pin it**:

```
F2 P5 re-enrollment — your personal enrollment link (30-day token)
Do not share outside this channel. A leaked link is fixed by reissuing it.

Shan    (DEMO-HCW-004)  <paste URL>
Kidd    (DEMO-HCW-007)  <paste URL>
Marriz  (DEMO-HCW-002)  <paste URL>
Aly     (DEMO-HCW-005)  <paste URL>
QN leg  (p5-qn-check)   <paste URL>
```

Then send the kickoff draft already sitting in that channel.

## Step 5 — Tell me

I'll tick the pre-flight boxes on **#836** and watch the round.

---

### Why you're doing this and not me

Authenticating to the admin API needs an admin identity. Every Administrator in the store is
a real person, so any session I mint stamps someone's name — most naturally yours — onto the
`f2_audit` rows for tokens *I* created. For a credential-issuing action on the authoritative
store, a true audit trail is worth five minutes of clicking. (If you'd rather I automate it
anyway, that's a legitimate call — say so naming the box and the action, and accept that the
audit reads `carl_admin`.)
