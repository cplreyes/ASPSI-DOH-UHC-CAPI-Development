# CAPI Training Decks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. **Git is Carl's to handle** — do NOT auto-commit. The real checkpoint for each task is *render the built `.pptx` to images and look at every slide*.

**Goal:** Build two presentation-ready `.pptx` decks — Field Supervisor and Field Enumerator — for Carl's named CAPI sessions in the August 2026 UHC Survey Year 2 trainings, composed from one shared module library.

**Architecture:** A single `modules.js` data file holds all slide content as plain data (one exported object per module A–L). Two thin builders (`build_fs_deck.js`, `build_fe_deck.js`) import it, select and order the modules their programme requires, and emit a `.pptx` through a shared `theme.js` (Verde Executive palette + layout helpers). Content is authored once; composition is the only thing that differs per deck.

**Tech Stack:** Node + `pptxgenjs` (run with `NODE_PATH="$(npm root -g)"`), Python 3 + PyMuPDF (render QA), LibreOffice Portable (pptx→pdf), `unzip` (screenshot extraction from the team manual).

## Global Constraints

- **Verde Executive palette, verbatim:** INK `0E3B2C` · emerald `1B6B4C` · gold `C9A227` · cream `F5F2E9` · body ink `1A241E`. **Georgia** titles, **Calibri** body. Gold slide numbers and eyebrows; section-pill motif.
- **Every content slide is a do-along:** assertion title → real tablet screen → "YOU DO" step strip → CHECK drill. One idea per slide.
- **No mockups.** Every screenshot is a real device capture from one of the three approved sources. **Zero unfilled placeholder boxes** in the delivered decks.
- **Images letterboxed, never stretched** — record each image's aspect ratio and fit within the box.
- **Server address taught is `capi.asiansocial.org/csweb/api`** (the console + sync API canonical host).
- **Escalation chain:** FE → FS → RA → Data Programmer (never IT direct). Enumerator deck stops at "report to your Field Supervisor".
- **Validation vocabulary:** Required / Soft Warning / Hard Warning. **Sync deadline:** daily by 10:00 PM.
- **F2 is taught as the manual describes it** (self-administered, monitored through CSWeb) — the live separate HCW console is a recorded discrepancy, not a teaching change.
- **Build to the job tmp directory and deliver with `SendUserFile`.** Never overwrite a file in Downloads — PowerPoint holds an EBUSY lock.
- Spec: `docs/superpowers/specs/2026-07-29-capi-training-decks-design.md`.

---

## File Structure

All build files live in `$CLAUDE_JOB_DIR/tmp/decks/` (ephemeral build workspace):

- `theme.js` — palette constants, master slide definitions, and the four layout helpers every content slide uses. One responsibility: *how a slide looks*.
- `modules.js` — the module library as data. Exports `MODULES` keyed `A`–`L`; each module is `{id, title, eyebrow, slides:[...]}`. One responsibility: *what the slides say*.
- `shots.js` — the screenshot registry: maps logical names (`login-username`, `f1-question`, …) to absolute file paths plus a recorded `{w,h}` aspect ratio. One responsibility: *where the images are and what shape they are*.
- `build_fs_deck.js` — composes the Field Supervisor deck.
- `build_fe_deck.js` — composes the Field Enumerator deck.
- `render_qa.py` — converts a built `.pptx` to per-slide PNGs for visual verification.

Final artefacts (delivered, not committed): `UHC-Y2-CAPI-Training-FieldSupervisors.pptx`, `UHC-Y2-CAPI-Training-FieldEnumerators.pptx`.

---

### Task 1: Screenshot registry — extract, inventory, record ratios

**Files:**
- Create: `$CLAUDE_JOB_DIR/tmp/decks/shots.js`
- Create: `$CLAUDE_JOB_DIR/tmp/decks/shots/` (extracted images)
- Read: `deliverables/CAPI-Manual/img/` (24 curated captures), `C:\Users\analy\Downloads\DOH_CAPI_Manual_July27.docx` (46 embedded captures)

**Interfaces:**
- Produces: `shots.js` exporting `SHOTS` = `{ <logicalName>: { path: <abs>, w: <px>, h: <px> } }`, and `has(name)`.

- [ ] **Step 1: Extract the team manual's embedded images**

```bash
D="$CLAUDE_JOB_DIR/tmp/decks/shots"; mkdir -p "$D/team"
unzip -o -j "/c/Users/analy/Downloads/DOH_CAPI_Manual_July27.docx" "word/media/*" -d "$D/team"
ls "$D/team" | wc -l   # expect ~46
```

- [ ] **Step 2: Map each team-manual image to its caption**

```bash
cd "$CLAUDE_JOB_DIR/tmp/decks"
pandoc "/c/Users/analy/Downloads/DOH_CAPI_Manual_July27.docx" -o team-manual.md
grep -n -B2 "media/image" team-manual.md | head -120
```

Record the mapping for the picks named in the spec: `image13`=Add Application, `image19`=install list, `image20`=Entry Applications menu, `image23`=enumerator hub (Send My Interviews), `image29`=case list with status bars, `image30`=live question screen, `image33`=FacilityHeadSurvey question, `image43`=F3 Patient-Type gate, `image2`=data-flow diagram. Confirm each against the caption context before trusting it.

- [ ] **Step 3: Copy the 24 curated CAPI-Manual captures**

```bash
cp "/c/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CAPI-Manual/img/"*.png "$CLAUDE_JOB_DIR/tmp/decks/shots/manual/" 2>/dev/null || \
  { mkdir -p "$CLAUDE_JOB_DIR/tmp/decks/shots/manual"; cp "/c/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CAPI-Manual/img/"*.png "$CLAUDE_JOB_DIR/tmp/decks/shots/manual/"; }
ls "$CLAUDE_JOB_DIR/tmp/decks/shots/manual" | wc -l   # expect 24
```

- [ ] **Step 4: Generate `shots.js` with real pixel dimensions**

```bash
cd "$CLAUDE_JOB_DIR/tmp/decks"
python - <<'PY'
import os, json
from PIL import Image
root = os.path.join(os.environ["CLAUDE_JOB_DIR"], "tmp", "decks", "shots")
rows = []
for sub in ("manual", "team"):
    d = os.path.join(root, sub)
    if not os.path.isdir(d): continue
    for fn in sorted(os.listdir(d)):
        if not fn.lower().endswith((".png", ".jpg", ".jpeg", ".emf", ".wmf")): continue
        p = os.path.join(d, fn)
        try: w, h = Image.open(p).size
        except Exception: continue          # skip vector/unreadable
        key = "%s_%s" % (sub, os.path.splitext(fn)[0].replace("-", "_").replace(".", "_"))
        rows.append((key, p.replace("\\", "/"), w, h))
with open("shots.js", "w", encoding="utf-8") as f:
    f.write("// generated by Task 1 — logical name -> {path, w, h}\nconst SHOTS = {\n")
    for k, p, w, h in rows:
        f.write('  %s: { path: "%s", w: %d, h: %d },\n' % (k, p, w, h))
    f.write("};\nfunction has(n){ return Object.prototype.hasOwnProperty.call(SHOTS, n); }\n")
    f.write("module.exports = { SHOTS, has };\n")
print("wrote shots.js with", len(rows), "images")
PY
```

- [ ] **Step 5: Verify the registry loads and every path exists**

```bash
cd "$CLAUDE_JOB_DIR/tmp/decks"
NODE_PATH="$(npm root -g)" node -e "
const fs=require('fs'); const {SHOTS}=require('./shots.js');
const names=Object.keys(SHOTS);
const missing=names.filter(n=>!fs.existsSync(SHOTS[n].path));
console.log('images registered:', names.length);
console.log('missing files   :', missing.length, missing.slice(0,5));
if(missing.length) process.exit(1);
"
```
Expected: ≥ 50 images registered, 0 missing.

---

### Task 2: Theme — palette, masters, and the four layout helpers

**Files:**
- Create: `$CLAUDE_JOB_DIR/tmp/decks/theme.js`

**Interfaces:**
- Consumes: `shots.js` (`SHOTS`, `has`).
- Produces: `newDeck()` → a configured `pptxgenjs` instance; and slide helpers
  `titleSlide(pptx,{title,subtitle,meta})`, `sectionSlide(pptx,{pill,title,blurb})`,
  `doAlongSlide(pptx,{eyebrow,assertion,shot,steps,check})`,
  `bulletSlide(pptx,{eyebrow,assertion,bullets,note})`.
  All helpers append a slide and return it.

- [ ] **Step 1: Write `theme.js`**

```javascript
const pptxgen = require("pptxgenjs");
const { SHOTS, has } = require("./shots.js");

const C = { ink:"0E3B2C", emerald:"1B6B4C", gold:"C9A227", cream:"F5F2E9", body:"1A241E", white:"FFFFFF" };
const F = { title:"Georgia", body:"Calibri" };
const W = 13.333, H = 7.5;                      // 16:9 inches

function newDeck(subject) {
  const p = new pptxgen();
  p.layout = "LAYOUT_16x9";
  p.author = "Carl Patrick L. Reyes";
  p.company = "ASPSI — DOH UHC Survey Year 2";
  p.subject = subject;
  return p;
}

function chrome(slide, eyebrow) {                // gold eyebrow + slide furniture
  if (eyebrow) slide.addText(eyebrow.toUpperCase(), {
    x:0.55, y:0.32, w:9, h:0.3, fontFace:F.body, fontSize:11, bold:true,
    color:C.gold, charSpacing:2 });
  slide.addShape("rect", { x:0, y:H-0.28, w:W, h:0.28, fill:{ color:C.cream } });
}

function titleSlide(pptx, { title, subtitle, meta }) {
  const s = pptx.addSlide();
  s.background = { color: C.ink };
  s.addText(title, { x:0.9, y:2.3, w:11.5, h:1.6, fontFace:F.title, fontSize:40, bold:true, color:C.white });
  if (subtitle) s.addText(subtitle, { x:0.9, y:3.9, w:11.5, h:0.8, fontFace:F.body, fontSize:20, color:C.gold });
  if (meta) s.addText(meta, { x:0.9, y:5.9, w:11.5, h:0.6, fontFace:F.body, fontSize:13, color:C.cream });
  return s;
}

function sectionSlide(pptx, { pill, title, blurb }) {
  const s = pptx.addSlide();
  s.background = { color: C.emerald };
  s.addShape("roundRect", { x:0.9, y:2.5, w:2.2, h:0.5, fill:{ color:C.gold }, rectRadius:0.25 });
  s.addText(pill, { x:0.9, y:2.5, w:2.2, h:0.5, align:"center", fontFace:F.body, fontSize:13, bold:true, color:C.ink });
  s.addText(title, { x:0.9, y:3.2, w:11.5, h:1.2, fontFace:F.title, fontSize:34, bold:true, color:C.white });
  if (blurb) s.addText(blurb, { x:0.9, y:4.5, w:10.5, h:0.9, fontFace:F.body, fontSize:16, color:C.cream });
  return s;
}

// letterbox: fit (w,h) inside the box, never stretch
function fit(shotName, bx, by, bw, bh) {
  const m = SHOTS[shotName];
  const r = m.w / m.h, br = bw / bh;
  let w = bw, h = bh;
  if (r > br) { h = bw / r; } else { w = bh * r; }
  return { path:m.path, x: bx + (bw - w)/2, y: by + (bh - h)/2, w, h };
}

function doAlongSlide(pptx, { eyebrow, assertion, shot, steps, check }) {
  const s = pptx.addSlide();
  s.background = { color: C.white };
  chrome(s, eyebrow);
  s.addText(assertion, { x:0.55, y:0.7, w:12.2, h:0.9, fontFace:F.title, fontSize:26, bold:true, color:C.ink });
  if (shot && has(shot)) s.addImage(fit(shot, 0.55, 1.75, 5.6, 4.6));
  else s.addShape("rect", { x:0.55, y:1.75, w:5.6, h:4.6, fill:{ color:C.cream } });
  s.addText("YOU DO", { x:6.5, y:1.75, w:6.2, h:0.35, fontFace:F.body, fontSize:12, bold:true, color:C.emerald, charSpacing:1.5 });
  s.addText(steps.map(t => ({ text:t, options:{ bullet:{ type:"number" }, breakLine:true } })),
    { x:6.5, y:2.15, w:6.2, h:2.9, fontFace:F.body, fontSize:15, color:C.body, lineSpacing:24 });
  if (check) {
    s.addShape("roundRect", { x:6.5, y:5.2, w:6.2, h:1.15, fill:{ color:C.cream }, rectRadius:0.1 });
    s.addText([{ text:"CHECK  ", options:{ bold:true, color:C.gold } }, { text:check, options:{ color:C.body } }],
      { x:6.7, y:5.35, w:5.8, h:0.85, fontFace:F.body, fontSize:13 });
  }
  return s;
}

function bulletSlide(pptx, { eyebrow, assertion, bullets, note }) {
  const s = pptx.addSlide();
  s.background = { color: C.white };
  chrome(s, eyebrow);
  s.addText(assertion, { x:0.55, y:0.7, w:12.2, h:0.9, fontFace:F.title, fontSize:26, bold:true, color:C.ink });
  s.addText(bullets.map(t => ({ text:t, options:{ bullet:true, breakLine:true } })),
    { x:0.55, y:1.9, w:12.2, h:3.9, fontFace:F.body, fontSize:17, color:C.body, lineSpacing:30 });
  if (note) s.addText(note, { x:0.55, y:5.95, w:12.2, h:0.6, fontFace:F.body, fontSize:13, italic:true, color:C.emerald });
  return s;
}

module.exports = { C, F, newDeck, titleSlide, sectionSlide, doAlongSlide, bulletSlide, fit };
```

- [ ] **Step 2: Smoke-test the theme by emitting a 4-slide sampler**

```bash
cd "$CLAUDE_JOB_DIR/tmp/decks"
NODE_PATH="$(npm root -g)" node -e "
const T=require('./theme.js'); const {SHOTS}=require('./shots.js');
const anyShot=Object.keys(SHOTS)[0];
const p=T.newDeck('theme smoke');
T.titleSlide(p,{title:'Theme smoke test',subtitle:'Verde Executive',meta:'ASPSI · UHC Y2'});
T.sectionSlide(p,{pill:'MODULE A',title:'Section slide',blurb:'Pill + title + blurb'});
T.doAlongSlide(p,{eyebrow:'Module A',assertion:'A do-along slide states a claim',shot:anyShot,steps:['First action','Second action','Third action'],check:'Did the screen change?'});
T.bulletSlide(p,{eyebrow:'Module A',assertion:'A bullet slide',bullets:['One','Two','Three'],note:'facilitator note'});
p.writeFile({fileName:'_smoke.pptx'}).then(()=>console.log('wrote _smoke.pptx'));
"
```
Expected: `wrote _smoke.pptx`, no exceptions.

- [ ] **Step 3: Render the sampler and LOOK at it** (this is the real test)

Run `render_qa.py` from Task 3 once it exists; for this step use it inline:
```bash
cd "$CLAUDE_JOB_DIR/tmp/decks"
"/c/xampp/LibreOfficePortable/App/LibreOffice64/program/soffice.com" --headless --convert-to pdf _smoke.pptx --outdir . 2>&1 | tail -1
python -c "
import fitz; d=fitz.open('_smoke.pdf')
[d[i].get_pixmap(dpi=110).save('_smoke_%d.png'%i) for i in range(d.page_count)]
print('rendered', d.page_count, 'pages')"
```
Then **Read each `_smoke_*.png`** and confirm: dark title slide, emerald section slide with gold pill, do-along slide with a *letterboxed* (not stretched) screenshot on the left and numbered steps on the right, bullet slide. Fix `theme.js` and re-render until it looks right.

---

### Task 3: Render-QA helper

**Files:**
- Create: `$CLAUDE_JOB_DIR/tmp/decks/render_qa.py`

**Interfaces:**
- Produces: CLI `python render_qa.py <deck.pptx> <outdir>` → writes `slide-01.png …`, prints the page count.

- [ ] **Step 1: Write `render_qa.py`**

```python
#!/usr/bin/env python3
"""Render a .pptx to per-slide PNGs so every slide can be visually verified.

LibreOffice Portable does the pptx->pdf step (the pptx skill's soffice.py wrapper
is AF_UNIX-only and fails on Windows); PyMuPDF rasterises (pdftoppm is absent).
"""
import os, subprocess, sys
import fitz

SOFFICE = r"C:/xampp/LibreOfficePortable/App/LibreOffice64/program/soffice.com"

def main():
    if len(sys.argv) != 3:
        sys.exit("usage: render_qa.py <deck.pptx> <outdir>")
    deck, outdir = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    os.makedirs(outdir, exist_ok=True)
    subprocess.run([SOFFICE, "--headless", "--convert-to", "pdf", deck,
                    "--outdir", outdir], check=True, timeout=600)
    pdf = os.path.join(outdir, os.path.splitext(os.path.basename(deck))[0] + ".pdf")
    if not os.path.exists(pdf):
        sys.exit("conversion produced no PDF: %s" % pdf)
    doc = fitz.open(pdf)
    for i in range(doc.page_count):
        doc[i].get_pixmap(dpi=110).save(os.path.join(outdir, "slide-%02d.png" % (i + 1)))
    print("rendered %d slides -> %s" % (doc.page_count, outdir))

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify against the smoke deck**

```bash
cd "$CLAUDE_JOB_DIR/tmp/decks" && python render_qa.py _smoke.pptx qa_smoke
```
Expected: `rendered 4 slides -> .../qa_smoke`.

---

### Task 4: Module library — spine modules A–D (Using CAPI / Installation)

**Files:**
- Create: `$CLAUDE_JOB_DIR/tmp/decks/modules.js` (modules A–D in this task)

**Interfaces:**
- Produces: `MODULES.A`…`MODULES.D`, each `{ id, title, eyebrow, section:{pill,title,blurb}, slides:[ {kind:"doalong"|"bullet", ...} ] }` where slide objects carry exactly the keys `doAlongSlide`/`bulletSlide` accept (minus `eyebrow`, which the builder injects from the module).

- [ ] **Step 1: Author modules A–D**

Content is fixed by the spec and the source manuals — write it verbatim, do not invent procedures. Key facts that MUST appear: server address `capi.asiansocial.org/csweb/api`; update by **remove + re-add**; validation vocabulary **Required / Soft Warning / Hard Warning**; suspend & resume auto-saves.

```javascript
// modules.js — the module library as data. Authored once; composed per deck.
const MODULES = {
  A: {
    id:"A", title:"Why CAPI", eyebrow:"Why CAPI",
    section:{ pill:"MODULE A", title:"Why we collect on a tablet",
              blurb:"What changes from paper — and what stays exactly the same." },
    slides:[
      { kind:"bullet", assertion:"The questions do not change. The way we record them does.",
        bullets:[
          "Same questionnaire, same wording, same order you learned on paper",
          "The tablet enforces the skips and the checks you used to do in your head",
          "Your work reaches the office the same day instead of weeks later",
          "Nothing is final until you complete and sync the case"],
        note:"Open by lowering the technology anxiety — the interview is still an interview." },
      { kind:"bullet", assertion:"Four instruments, four different jobs.",
        bullets:[
          "F1 Facility Head — face-to-face on the tablet, about the facility (~1 hour)",
          "F2 Health Care Worker — self-administered online by the respondent (~30 min)",
          "F3 Patient — face-to-face on the tablet, inpatient and outpatient (~1 hour)",
          "F4 Household — face-to-face on the tablet, household roster and expenditures"],
        note:"F2 is the odd one out: you hand over a link, you do not interview." }
    ]
  },
  B: {
    id:"B", title:"Install and connect", eyebrow:"Install & connect",
    section:{ pill:"MODULE B", title:"Getting the survey onto your tablet",
              blurb:"One address, one install, one way to update." },
    slides:[
      { kind:"doalong", assertion:"CSEntry downloads the survey from our server, not from a store.",
        shot:"team_image13",
        steps:["Open CSEntry on the tablet",
               "Tap the menu, then Add Application",
               "Choose From CSWeb server",
               "Type the address exactly: capi.asiansocial.org/csweb/api"],
        check:"Does the server list show the UHC Year 2 applications?" },
      { kind:"doalong", assertion:"Install every application you are assigned — not just one.",
        shot:"team_image19",
        steps:["Tick each application listed for your role",
               "Tap Add / Install and wait for each to finish",
               "Return to the Entry Applications list",
               "Confirm each one appears with no error"],
        check:"Count the applications on your screen — does it match your assignment?" },
      { kind:"bullet", assertion:"To update, remove the app and add it again.",
        bullets:[
          "The menu's Update Installed Applications is unreliable — it often reports no update",
          "The dependable route: remove the application, then Add Application from CSWeb again",
          "Your completed cases are not lost by removing an application — they are already saved",
          "Always re-add before starting a new day if you were told a new version was published"],
        note:"This is the single most common false alarm in the field. Teach it once, firmly." }
    ]
  },
  C: {
    id:"C", title:"Login and your assignment", eyebrow:"Login & assignment",
    section:{ pill:"MODULE C", title:"Signing in and finding your work",
              blurb:"Your login decides what you see." },
    slides:[
      { kind:"doalong", assertion:"You sign in as yourself — the app then shows only your work.",
        shot:"manual_04_02_username",
        steps:["Open the login application",
               "Enter the username issued to you",
               "Enter your password",
               "Tap OK"],
        check:"Does the menu show your own name and role?" },
      { kind:"doalong", assertion:"An unknown username is a typing problem, not a broken tablet.",
        shot:"manual_04_login_error",
        steps:["Read the message on the screen",
               "Check for a stray space or a wrong dash in the username",
               "Try again carefully",
               "If it still fails, tell your Field Supervisor"],
        check:"What is the exact wording of the error you get?" },
      { kind:"doalong", assertion:"Your case list is your day's work.",
        shot:"team_image29",
        steps:["Open the instrument you are assigned",
               "Look at the case list and its status bars",
               "Identify which cases are new, in progress and completed",
               "Open a new case to begin"],
        check:"How many cases are waiting for you right now?" }
    ]
  },
  D: {
    id:"D", title:"Navigating a questionnaire", eyebrow:"Navigating",
    section:{ pill:"MODULE D", title:"Moving through the questions",
              blurb:"What the tablet does for you, and what it will not let you do." },
    slides:[
      { kind:"doalong", assertion:"Read the question as written; record what you hear.",
        shot:"team_image30",
        steps:["Read the question exactly as it appears",
               "Tap the answer the respondent gives",
               "Move forward with the next arrow",
               "Use the back arrow if you must correct an earlier answer"],
        check:"Did the tablet skip a question you expected? That is the skip logic working." },
      { kind:"bullet", assertion:"Three kinds of message, three different responses.",
        bullets:[
          "Required — the question must be answered before you can move on",
          "Soft Warning — unusual but possible; confirm with the respondent, then accept or correct",
          "Hard Warning — impossible; you cannot continue until it is fixed",
          "Never invent a value to escape a message — ask the respondent again"],
        note:"Have trainees trigger each of the three deliberately during the drill." },
      { kind:"bullet", assertion:"Don't Know and Refused are real answers. Blank is not.",
        bullets:[
          "If the respondent does not know, record Don't Know — do not guess",
          "If the respondent declines, record Refused — do not persuade",
          "Never leave an item empty to 'come back later'",
          "An interrupted interview is suspended and resumes exactly where you stopped"],
        note:"Ties directly to the pre/post exam item on 'I don't know' answers." }
    ]
  }
};
module.exports = { MODULES };
```

- [ ] **Step 2: Verify the four modules load and are well-formed**

```bash
cd "$CLAUDE_JOB_DIR/tmp/decks"
NODE_PATH="$(npm root -g)" node -e "
const {MODULES}=require('./modules.js'); const {has}=require('./shots.js');
for (const k of ['A','B','C','D']) {
  const m=MODULES[k];
  if(!m) throw new Error('missing module '+k);
  if(!m.section||!m.slides.length) throw new Error('module '+k+' incomplete');
  m.slides.forEach((s,i)=>{
    if(!s.assertion) throw new Error(k+' slide '+i+' has no assertion');
    if(s.kind==='doalong'){
      if(!s.steps||!s.steps.length) throw new Error(k+' slide '+i+' has no steps');
      if(s.shot && !has(s.shot)) console.log('  WARN missing shot:',k,i,s.shot);
    }
  });
  console.log(' module',k,'ok —',m.slides.length,'slides');
}"
```
Expected: four `ok` lines. **Any `WARN missing shot` must be resolved** — either correct the logical name against `shots.js` or pick a different real capture. Do not leave a do-along slide without an image.

---

### Task 5: Module library — instrument modules E, F, G, H

**Files:**
- Modify: `$CLAUDE_JOB_DIR/tmp/decks/modules.js` (add E–H)

**Interfaces:**
- Consumes: the module object shape from Task 4.
- Produces: `MODULES.E` (F1), `MODULES.F` (F2), `MODULES.G` (F3), `MODULES.H` (F4).

Section spines are **real, read from the deployed CSPro form files** — use exactly these:

- **F1 (13):** Case Key → Geo ID → A Facility Head Profile → B Facility Profile → C UHC Implementation → D YAKAP/Konsulta → E BUCAS & GAMOT → F DOH Licensing → G Service Delivery → H HR for Health → Field Control → Verification Photo → Facility GPS.
- **F3:** Case Key → **Patient Type gate** → Geo/F1 link → A Consent → B Profile → C UHC Awareness → D PhilHealth → E Primary Care/YAKAP → F Health-Seeking → **G Outpatient / H Inpatient (branch, cost matrices)** → I Financial Risk → J Satisfaction → K Access to Medicines → L Referrals → Photo → GPS.
- **F4 (56 forms, A–Q):** Case Key → Interview status → FC Geographic ID → A Informed Consent (Q1 gate) → B Respondent Profile → **C Household roster (23 repeating forms — name, present, age, sex, relationship, disability + PWD card, civil status, education, employment, GSIS/SSS/Pag-IBIG, PhilHealth + registration date / why-not, member category, private insurance)** → D UHC Awareness → E YAKAP/Konsulta → F BUCAS Awareness → G Access to Medicines → H PhilHealth Registration → I Primary Care → J Health Seeking → K Referrals → L NBB Awareness → M ZBB/MAIFIP/Bill-Recall → **N Expenditures (12 forms across reference periods: food last week, household expenditures, restaurant+tobacco last week, non-food last month / 6 months / 12 months, health 12/6/1 months each with a subtotal)** → O Sources of Funds for Health → P Financial Risk → Q Financial Anxiety → Verification Photo → HH GPS Capture.
- **F2:** self-administered, sections A–J; the respondent opens a link or QR and answers on their own device; **taught as monitored through CSWeb** per the manual.

- [ ] **Step 1: Author modules E–H**

Each instrument module follows the same four-beat shape: *what this instrument is and who answers it* → *the section spine* → *the one hard part* → *the mock-interview drill*. The "one hard part" per instrument: **F1** the Field Control block and the photo/GPS tail; **F2** that you never interview — you hand over a link and monitor completion; **F3** the Patient-Type gate that branches the whole rest of the interview into Outpatient (G) or Inpatient (H); **F4** the roster in Section C (one row per member, every attribute asked for every person) and the reference periods in Section N.

Append to `modules.js` before `module.exports`:

```javascript
MODULES.E = {
  id:"E", title:"F1 — Facility Head", eyebrow:"F1 Facility Head",
  section:{ pill:"MODULE E", title:"F1 — the Facility Head interview",
            blurb:"One facility, one head, thirteen sections — and the full case lifecycle." },
  slides:[
    { kind:"bullet", assertion:"F1 asks the facility about itself, through the person who runs it.",
      bullets:["Respondent: the officer in charge of the health facility",
               "Face-to-face on your tablet, about one hour",
               "Covers capacity, staffing, licensing, supplies, referrals",
               "Ends with a verification photo and a GPS reading of the facility"],
      note:"F1 is the first instrument taught because it carries the whole lifecycle." },
    { kind:"bullet", assertion:"Thirteen sections, in this order, every time.",
      bullets:["Case Key · Geographic ID",
               "A Facility Head Profile · B Facility Profile · C UHC Implementation",
               "D YAKAP/Konsulta · E BUCAS & GAMOT · F DOH Licensing",
               "G Service Delivery · H Human Resources for Health",
               "Field Control · Verification Photo · Facility GPS"],
      note:"Read from the deployed application, not the paper questionnaire." },
    { kind:"doalong", assertion:"Start a case by entering its key — the key identifies the facility.",
      shot:"team_image33",
      steps:["Open the Facility Head application",
             "Start a new case","Enter the case key for your assigned facility",
             "Confirm the geographic identifiers that appear"],
      check:"Does the facility shown match your assignment sheet?" },
    { kind:"doalong", assertion:"The photo and the GPS come last — and the case is not done without them.",
      shot:"manual_04_04_enumerator_menu",
      steps:["Complete the Field Control block",
             "Take the verification photo when prompted",
             "Wait for the GPS reading to settle before accepting it",
             "Complete the case"],
      check:"Did you wait for the GPS, or accept the first reading?" },
    { kind:"bullet", assertion:"Drill: run one complete F1 case, end to end.",
      bullets:["Pair up: one interviews, one observes",
               "Interviewer: start a case and complete two sections",
               "Observer: score introduction, ethics, neutrality, probing, thanks",
               "Swap roles and repeat"],
      note:"Mock interview — the programme's stated assessment for this day." }
  ]
};

MODULES.F = {
  id:"F", title:"F2 — Health Care Worker", eyebrow:"F2 Health Care Worker",
  section:{ pill:"MODULE F", title:"F2 — the one you do not interview",
            blurb:"Self-administered by the health worker, on their own device." },
  slides:[
    { kind:"bullet", assertion:"For F2 you are a facilitator, not an interviewer.",
      bullets:["The health care worker answers for themselves, in their own time",
               "They open a link or scan a QR code — it is not in CSEntry",
               "About 30 minutes, on their own phone or a shared device",
               "Your job is to explain it, hand it over, and follow up"],
      note:"This is the single biggest misconception to correct early." },
    { kind:"bullet", assertion:"Sections A to J, answered by the worker themselves.",
      bullets:["Profile and employment","Practice and workload","Referrals and networks",
               "Task sharing","Compensation and satisfaction","Intention to leave"],
      note:"Trainees should open the link once themselves so they can answer questions about it." },
    { kind:"bullet", assertion:"Completion is monitored, so follow-up is part of the job.",
      bullets:["Completions are monitored through CSWeb",
               "Target: at least 60 percent of the facility's master list",
               "If completion is at or below 40 percent by the three-day midpoint, the Field Supervisor follows up",
               "Never fill in the survey on a worker's behalf"],
      note:"Per the survey manual. Flag to Myra: the live system also has a separate HCW console." }
  ]
};

MODULES.G = {
  id:"G", title:"F3 — Patients", eyebrow:"F3 Patients",
  section:{ pill:"MODULE G", title:"F3 — inpatients and outpatients",
            blurb:"One instrument, two paths — chosen at the very start." },
  slides:[
    { kind:"bullet", assertion:"F3 interviews the patient about their own care experience.",
      bullets:["Respondent: a patient at the sampled facility",
               "Face-to-face on your tablet, about one hour",
               "Two respondent types: inpatient and outpatient",
               "Covers awareness, PhilHealth, costs, satisfaction, medicines, referrals"] },
    { kind:"doalong", assertion:"The Patient Type gate decides the rest of the interview.",
      shot:"team_image43",
      steps:["Start a new F3 case",
             "Answer the Patient Type question truthfully for this respondent",
             "Notice which sections the tablet now offers you",
             "Do not go back and change it mid-interview"],
      check:"Outpatients get Section G; inpatients get Section H. Which did you get?" },
    { kind:"bullet", assertion:"The cost questions are where accuracy matters most.",
      bullets:["Section G (outpatient) and Section H (inpatient) carry the cost matrices",
               "Ask for each cost separately — do not accept a single lump figure",
               "Zero is a valid answer; blank is not",
               "Use Don't Know when the respondent genuinely does not know"],
      note:"These feed the financial-risk and catastrophic-expenditure analysis." },
    { kind:"bullet", assertion:"Drill: one outpatient case and one inpatient case.",
      bullets:["Pair up and run an outpatient case through the gate and Section G",
               "Swap, then run an inpatient case through the gate and Section H",
               "Observer scores the five behaviours",
               "Compare: what changed between the two paths?"],
      note:"Mock interview." }
  ]
};

MODULES.H = {
  id:"H", title:"F4 — Household", eyebrow:"F4 Household",
  section:{ pill:"MODULE H", title:"F4 — the household interview",
            blurb:"The longest instrument: a roster of people, then a year of spending." },
  slides:[
    { kind:"bullet", assertion:"F4 asks one respondent about the whole household.",
      bullets:["Respondent: a knowledgeable adult member of the sampled household",
               "Face-to-face on your tablet — the longest of the four instruments",
               "Consent is asked first and gates everything after it",
               "Ends with a verification photo and a household GPS reading"] },
    { kind:"bullet", assertion:"Seventeen sections, A through Q.",
      bullets:["A Consent · B Respondent Profile · C Household Roster",
               "D UHC Awareness · E YAKAP/Konsulta · F BUCAS · G Access to Medicines",
               "H PhilHealth Registration · I Primary Care · J Health Seeking · K Referrals",
               "L NBB Awareness · M ZBB/MAIFIP · N Expenditures",
               "O Sources of Funds · P Financial Risk · Q Financial Anxiety"],
      note:"Read from the deployed application (56 forms)." },
    { kind:"bullet", assertion:"Section C is a roster: every question is asked for every member.",
      bullets:["First list everyone: name, and whether they are present",
               "Then the tablet walks each person through the same attributes in turn",
               "Age, sex, relationship to head, disability and PWD card, civil status",
               "Education, employment, GSIS/SSS/Pag-IBIG, PhilHealth and member category",
               "Do not skip a person because they are absent — absent members are still listed"],
      note:"The roster is the hardest CAPI concept in the whole survey. Slow down here." },
    { kind:"bullet", assertion:"Section N asks the same kind of question over different time windows.",
      bullets:["Food last week · restaurant and tobacco last week",
               "Non-food last month, last 6 months, last 12 months",
               "Health spending over 12 months, 6 months and 1 month — each with a subtotal",
               "Always repeat the reference period out loud with the question"],
      note:"The reference period is part of the question. Reading it changes the answer." },
    { kind:"bullet", assertion:"Drill: build a roster, then walk one expenditure block.",
      bullets:["Pair up: list a household of four, including one absent member",
               "Walk the roster through to the end for every person",
               "Then complete the food-last-week block",
               "Observer checks: was the reference period read every time?"],
      note:"Mock interview." }
  ]
};
```

- [ ] **Step 2: Verify E–H load, and that no do-along slide lost its image**

```bash
cd "$CLAUDE_JOB_DIR/tmp/decks"
NODE_PATH="$(npm root -g)" node -e "
const {MODULES}=require('./modules.js'); const {has}=require('./shots.js');
let bad=0;
for (const k of ['E','F','G','H']) {
  const m=MODULES[k]; if(!m) throw new Error('missing '+k);
  m.slides.forEach((s,i)=>{ if(s.kind==='doalong'&&s.shot&&!has(s.shot)){console.log('  MISSING SHOT',k,i,s.shot);bad++;} });
  console.log(' module',k,'ok —',m.slides.length,'slides');
}
if(bad) process.exit(1);"
```
Expected: four `ok` lines, exit 0.

---

### Task 6: Module library — lifecycle modules I, J, K and supervisor module L

**Files:**
- Modify: `$CLAUDE_JOB_DIR/tmp/decks/modules.js` (add I–L)

**Interfaces:**
- Produces: `MODULES.I` (completing), `MODULES.J` (sync), `MODULES.K` (troubleshooting/escalation), `MODULES.L` (monitoring — FS pack only).

- [ ] **Step 1: Author modules I–L**

```javascript
MODULES.I = {
  id:"I", title:"Completing a case", eyebrow:"Completing",
  section:{ pill:"MODULE I", title:"Finishing a case properly",
            blurb:"A case is not finished until you say how it ended." },
  slides:[
    { kind:"bullet", assertion:"Review before you complete — the tablet will not do it for you.",
      bullets:["Check that every section you visited is answered",
               "Resolve any outstanding warnings",
               "Confirm the photo and GPS were captured where required",
               "Only then mark the case complete"],
      note:"Exam item: review the questionnaire for completeness and accuracy before submitting." },
    { kind:"bullet", assertion:"Every case ends with a result — including the ones that did not happen.",
      bullets:["Completed — the interview was finished",
               "Partial — started but not finished; record why",
               "Not completed — record the result of visit honestly",
               "A refusal or an absent respondent is a valid, reportable outcome"],
      note:"Never delete a case to make the numbers look better." }
  ]
};

MODULES.J = {
  id:"J", title:"Sync to CSWeb", eyebrow:"Sync",
  section:{ pill:"MODULE J", title:"Sending your work to the office",
            blurb:"Every day, by ten in the evening." },
  slides:[
    { kind:"doalong", assertion:"Sync every day by 10:00 PM — not at the end of the week.",
      shot:"team_image23",
      steps:["Connect the tablet to the internet",
             "Open the menu and choose to send your interviews",
             "Wait for the confirmation — do not close the app mid-sync",
             "Check that the cases you sent now show as sent"],
      check:"How many cases did the confirmation say were sent?" },
    { kind:"bullet", assertion:"If the sync fails, your data is safe — report it, do not repeat the interview.",
      bullets:["Completed interviews stay on the tablet until they upload successfully",
               "Do not delete a case that failed to send",
               "Do not re-interview the respondent",
               "Tell your Field Supervisor and follow the troubleshooting steps"],
      note:"Exam item, word for word: inform the Field Supervisor and follow troubleshooting procedures." }
  ]
};

MODULES.K = {
  id:"K", title:"Troubleshooting and escalation", eyebrow:"Troubleshooting",
  section:{ pill:"MODULE K", title:"When something goes wrong",
            blurb:"There is always a next step — and always someone to tell." },
  slides:[
    { kind:"bullet", assertion:"Most field problems have the same four causes.",
      bullets:["No internet — sync later, keep interviewing offline",
               "Wrong username or password — check the characters, then ask your supervisor",
               "No application in the list — remove and add it again from the server",
               "A warning you cannot clear — re-ask the question; do not invent a value"],
      note:"Have trainees produce each of these deliberately during the drill." },
    { kind:"bullet", assertion:"Escalate in order. Never jump the chain.",
      bullets:["Field Enumerator reports to the Field Supervisor",
               "Field Supervisor escalates to the Research Associate",
               "Research Associate escalates to the Data Programmer",
               "Never contact IT support directly"],
      note:"FE deck stops at 'report to your Field Supervisor'." }
  ]
};

MODULES.L = {
  id:"L", title:"Monitoring from CAPI data", eyebrow:"Monitoring",
  section:{ pill:"MODULE L", title:"Watching fieldwork from the data",
            blurb:"What supervisors can see once cases start arriving." },
  slides:[
    { kind:"doalong", assertion:"Every synced case appears on the monitoring console the same day.",
      shot:"manual_05_coverage_report",
      steps:["Open the console in a browser and sign in",
             "Open the sync dashboard",
             "Filter to your own area",
             "Read completed against target for each facility"],
      check:"How many cases has your team sent today?" },
    { kind:"bullet", assertion:"Three questions the console answers for you every morning.",
      bullets:["Are cases arriving — and from whom?",
               "Are we on target for each facility and area?",
               "Is anything wrong with the data — missing GPS, duplicates, cases outside the plan?"],
      note:"Supports the daily review and progress-reporting modules." },
    { kind:"bullet", assertion:"Use it before the daily debrief, not after the week ends.",
      bullets:["Check arrivals and coverage each morning",
               "Follow up any enumerator who sent nothing yesterday",
               "Review flagged cases with the enumerator who collected them",
               "Bring the numbers to the weekly team meeting"],
      note:"Handoff pack — the programme assigns Day-3 monitoring to the Project Team." }
  ]
};
```

- [ ] **Step 2: Verify the complete library — all twelve modules**

```bash
cd "$CLAUDE_JOB_DIR/tmp/decks"
NODE_PATH="$(npm root -g)" node -e "
const {MODULES}=require('./modules.js'); const {has}=require('./shots.js');
const want='ABCDEFGHIJKL'.split(''); let slides=0,bad=0;
want.forEach(k=>{ const m=MODULES[k];
  if(!m) throw new Error('MISSING MODULE '+k);
  m.slides.forEach((s,i)=>{ if(!s.assertion){console.log(' no assertion',k,i);bad++;}
    if(s.kind==='doalong'&&s.shot&&!has(s.shot)){console.log(' MISSING SHOT',k,i,s.shot);bad++;} });
  slides+=m.slides.length; });
console.log('modules:',want.length,' content slides:',slides,' problems:',bad);
if(bad) process.exit(1);"
```
Expected: 12 modules, ~40 content slides, 0 problems.

---

### Task 7: Compose and render the Field Supervisor deck

**Files:**
- Create: `$CLAUDE_JOB_DIR/tmp/decks/build_fs_deck.js`

**Interfaces:**
- Consumes: `theme.js`, `modules.js`, `shots.js`.
- Produces: `UHC-Y2-CAPI-Training-FieldSupervisors.pptx`.

- [ ] **Step 1: Write the FS builder**

Composition per the spec (F1 carries the lifecycle: E + I + J + K):

```javascript
const T = require("./theme.js");
const { MODULES } = require("./modules.js");

// Field Supervisor — Day 2, Los Baños, August 2026
const PLAN = [
  { slot:"08:00 – 09:00 · Module 6: Using CAPI",              mods:["A","B","C","D"] },
  { slot:"09:00 – 10:30 · Walkthrough — Facility Head (F1)",  mods:["E","I","J","K"] },
  { slot:"10:30 – 12:00 · Walkthrough — Health Care Worker (F2)", mods:["F"] },
  { slot:"13:00 – 14:30 · Walkthrough — Patients (in/out)",   mods:["G"] },
  { slot:"14:30 – 16:00 · Walkthrough — Household (F4)",      mods:["H"] },
];

function addModule(pptx, m) {
  T.sectionSlide(pptx, m.section);
  m.slides.forEach(s => {
    const base = Object.assign({ eyebrow: m.eyebrow }, s);
    if (s.kind === "doalong") T.doAlongSlide(pptx, base);
    else T.bulletSlide(pptx, base);
  });
}

const pptx = T.newDeck("CAPI training — Field Supervisors");
T.titleSlide(pptx, {
  title:"Using CAPI",
  subtitle:"Field Supervisors Training · Day 2",
  meta:"UHC Survey Year 2 · ASPSI for DOH · Los Baños, Laguna · August 2026 · Carl Patrick L. Reyes" });

PLAN.forEach(block => {
  T.sectionSlide(pptx, { pill:"SESSION", title:block.slot, blurb:"" });
  block.mods.forEach(k => addModule(pptx, MODULES[k]));
});

T.titleSlide(pptx, { title:"Questions", subtitle:"Then: hands-on practice",
  meta:"Escalation — Field Enumerator → Field Supervisor → Research Associate → Data Programmer" });

pptx.writeFile({ fileName:"UHC-Y2-CAPI-Training-FieldSupervisors.pptx" })
    .then(f => console.log("wrote", f));
```

- [ ] **Step 2: Build it**

```bash
cd "$CLAUDE_JOB_DIR/tmp/decks" && NODE_PATH="$(npm root -g)" node build_fs_deck.js
```
Expected: `wrote UHC-Y2-CAPI-Training-FieldSupervisors.pptx`.

- [ ] **Step 3: Render every slide and inspect them**

```bash
cd "$CLAUDE_JOB_DIR/tmp/decks" && python render_qa.py UHC-Y2-CAPI-Training-FieldSupervisors.pptx qa_fs
```
Then **Read a spread of `qa_fs/slide-*.png`** — the title, one section slide, at least three do-along slides (one per instrument), and the last slide. Verify: no text overflowing its box, no stretched screenshots, no empty cream rectangle where an image should be, gold eyebrow present on content slides. Fix and rebuild until clean.

- [ ] **Step 4: Assert the deck's shape programmatically**

```bash
cd "$CLAUDE_JOB_DIR/tmp/decks"
python - <<'PY'
import zipfile, re
z = zipfile.ZipFile("UHC-Y2-CAPI-Training-FieldSupervisors.pptx")
slides = [n for n in z.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n)]
media  = [n for n in z.namelist() if n.startswith("ppt/media/")]
print("slides:", len(slides), " embedded media:", len(media))
assert len(slides) >= 30, "deck too short — check composition"
assert len(media) >= 8, "too few images embedded — do-along slides are missing screenshots"
print("FS deck shape OK")
PY
```

---

### Task 8: Compose and render the Field Enumerator deck

**Files:**
- Create: `$CLAUDE_JOB_DIR/tmp/decks/build_fe_deck.js`

**Interfaces:**
- Consumes: `theme.js`, `modules.js`, `shots.js`.
- Produces: `UHC-Y2-CAPI-Training-FieldEnumerators.pptx`.

- [ ] **Step 1: Write the FE builder**

Differences from FS, per the spec: Module 9 framing; **no Module L**; Household moves to Day 3; module K stops at the Field Supervisor; extended drill slides because the FE slots are much longer (F1 180 min vs 90; Household 240 vs 90).

```javascript
const T = require("./theme.js");
const { MODULES } = require("./modules.js");

// Field Enumerator — Day 2 and Day 3, four cluster venues
const PLAN = [
  { slot:"DAY 2 · 08:00 – 09:00 · Module 9: CAPI Installation",     mods:["A","B","C","D"] },
  { slot:"DAY 2 · 09:00 – 12:00 · Walkthrough — Facility Head (F1)", mods:["E","I","J","K"] },
  { slot:"DAY 2 · 13:00 – 15:00 · Walkthrough — Health Care Worker (F2)", mods:["F"] },
  { slot:"DAY 2 · 15:00 – 17:00 · Walkthrough — Patients (in/out)",  mods:["G"] },
  { slot:"DAY 3 · 08:00 – 12:00 · Walkthrough — Household (F4)",     mods:["H"] },
];

// The enumerator slots are 2–3x longer, so each instrument gets an extra practice slide.
const EXTRA_DRILL = {
  E:{ assertion:"Second drill: a case that does not go smoothly.",
      bullets:["Start a case, then suspend it midway and resume it",
               "Trigger a Hard Warning deliberately and clear it correctly",
               "Record a Don't Know and a Refused",
               "Complete the case and check it in the case list"],
      note:"Error paths are performed, not demonstrated." },
  G:{ assertion:"Second drill: switch respondent type.",
      bullets:["Run a second case with the opposite patient type",
               "Walk the cost matrix item by item",
               "Practise asking for each cost separately",
               "Observer scores the five behaviours again"], note:"" },
  H:{ assertion:"Second drill: a harder household.",
      bullets:["List a household of six with two absent members",
               "Include one member with a disability and a PWD card",
               "Complete two different expenditure reference periods",
               "Check every person reached the end of the roster"], note:"" },
};

function addModule(pptx, m) {
  T.sectionSlide(pptx, m.section);
  m.slides.forEach(s => {
    const base = Object.assign({ eyebrow: m.eyebrow }, s);
    if (s.kind === "doalong") T.doAlongSlide(pptx, base);
    else T.bulletSlide(pptx, base);
  });
  if (EXTRA_DRILL[m.id]) T.bulletSlide(pptx, Object.assign({ eyebrow:m.eyebrow }, EXTRA_DRILL[m.id]));
}

const pptx = T.newDeck("CAPI training — Field Enumerators");
T.titleSlide(pptx, {
  title:"CAPI Installation and the Survey Tools",
  subtitle:"Field Enumerators Training · Days 2 and 3",
  meta:"UHC Survey Year 2 · ASPSI for DOH · August 2026 · Carl Patrick L. Reyes" });

PLAN.forEach(block => {
  T.sectionSlide(pptx, { pill:"SESSION", title:block.slot, blurb:"" });
  block.mods.forEach(k => addModule(pptx, MODULES[k]));
});

T.titleSlide(pptx, { title:"Questions", subtitle:"Then: hands-on practice",
  meta:"If anything goes wrong in the field — tell your Field Supervisor." });

pptx.writeFile({ fileName:"UHC-Y2-CAPI-Training-FieldEnumerators.pptx" })
    .then(f => console.log("wrote", f));
```

- [ ] **Step 2: Build it**

```bash
cd "$CLAUDE_JOB_DIR/tmp/decks" && NODE_PATH="$(npm root -g)" node build_fe_deck.js
```
Expected: `wrote UHC-Y2-CAPI-Training-FieldEnumerators.pptx`.

- [ ] **Step 3: Render and inspect**

```bash
cd "$CLAUDE_JOB_DIR/tmp/decks" && python render_qa.py UHC-Y2-CAPI-Training-FieldEnumerators.pptx qa_fe
```
**Read a spread of `qa_fe/slide-*.png`** as in Task 7 Step 3, plus the three extra-drill slides. Confirm **Module L does not appear** anywhere in this deck.

- [ ] **Step 4: Assert deck shape and the FS/FE difference**

```bash
cd "$CLAUDE_JOB_DIR/tmp/decks"
python - <<'PY'
import zipfile, re
def texts(p):
    z=zipfile.ZipFile(p); out=[]
    for n in sorted(z.namelist()):
        if re.match(r"ppt/slides/slide\d+\.xml$", n):
            out.append(re.sub(r"<[^>]+>", " ", z.read(n).decode("utf-8", "ignore")))
    return out
fs, fe = texts("UHC-Y2-CAPI-Training-FieldSupervisors.pptx"), texts("UHC-Y2-CAPI-Training-FieldEnumerators.pptx")
print("FS slides:", len(fs), " FE slides:", len(fe))
join_fs, join_fe = " ".join(fs), " ".join(fe)
assert "Monitoring from the data" in join_fs or "Watching fieldwork" in join_fs, "FS deck missing Module L"
assert "Watching fieldwork" not in join_fe, "Module L leaked into the FE deck"
assert "Module 6" in join_fs and "Module 9" in join_fe, "session framing wrong"
assert "capi.asiansocial.org/csweb/api" in join_fs and "capi.asiansocial.org/csweb/api" in join_fe, "server address missing"
for k in ("Household", "Patient Type", "roster", "Refused", "10:00 PM"):
    assert k in join_fs and k in join_fe, "missing required content: %s" % k
print("composition assertions OK")
PY
```
Expected: both decks present, all assertions pass.

---

### Task 9: Final verification and delivery

**Files:** none created — verification and handoff.

- [ ] **Step 1: Confirm no placeholder boxes survived**

Every do-along slide must carry a real image. A cream rectangle means a missing shot.
```bash
cd "$CLAUDE_JOB_DIR/tmp/decks"
NODE_PATH="$(npm root -g)" node -e "
const {MODULES}=require('./modules.js'); const {has}=require('./shots.js');
let n=0,missing=0;
Object.values(MODULES).forEach(m=>m.slides.forEach(s=>{
  if(s.kind==='doalong'){n++; if(!s.shot||!has(s.shot)) missing++;}}));
console.log('do-along slides:',n,' without a real image:',missing);
if(missing) process.exit(1);"
```

- [ ] **Step 2: Read the full render of both decks one final time**

Render both (Tasks 7/8 step 3 produce `qa_fs/` and `qa_fe/`) and read **every** slide image. This is the acceptance gate — the decks are presentation-ready, so a slide that merely *builds* is not sufficient. Look for: text overflow, orphaned headings, stretched images, wrong eyebrow, missing CHECK box on drill slides.

- [ ] **Step 3: Deliver both decks to Carl**

Use `SendUserFile` with both `.pptx` paths and a caption naming the audience, session mapping and slide counts. **Do not write into `Downloads`** — PowerPoint may hold a lock.

- [ ] **Step 4: Record what shipped**

Append a `log.md` entry in the project root: what was built, the module/slide counts, the screenshot sources used, the composition per deck, and the open items carried from the spec (F2 monitoring discrepancy; the FE F2 slot with no named in-charge; the sync-URL cutover dependency).

---

## Self-Review

**1. Spec coverage.** §2 benchmark → the module shape and drill-per-module rule (Tasks 4–6). §3.1 library A–L → Tasks 4, 5, 6. §3.2 FS composition incl. the F1-carries-lifecycle fix → Task 7. §3.3 FE composition + extended drills → Task 8. §4 slide grammar → `theme.js` helpers (Task 2). §5 build/palette/screenshots/render-QA/delivery → Tasks 1, 2, 3, 9. §6 decisions: server address (Global Constraints + Task 8 assertion), Module L as FS-only pack (Tasks 6, 8 assertion), F2 taught per the manual (Module F), FE F2 in-charge question (Task 9 step 4). §7 success criteria → Task 9. **No gaps.**

**2. Placeholder scan.** Every step carries real code or a real command. No TBD/TODO. The one "author the content" instruction (Tasks 4–6) is accompanied by the complete content inline, not a description of it.

**3. Type consistency.** `theme.js` exports `newDeck/titleSlide/sectionSlide/doAlongSlide/bulletSlide/fit/C/F` — used under exactly those names in Tasks 7 and 8. `shots.js` exports `{SHOTS, has}`; `has()` is used in Tasks 4, 5, 6, 9 and inside `theme.js`. `modules.js` exports `{MODULES}`; every module object carries `{id,title,eyebrow,section,slides}` and every slide `{kind, assertion, ...}` — the shape both builders consume. `render_qa.py` CLI signature matches every invocation.
