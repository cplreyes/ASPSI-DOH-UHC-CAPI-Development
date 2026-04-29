---
type: deliverable
kind: email-draft
audience: Juvy (ASPSI procurement)
sender: Carl Patrick L. Reyes
date_drafted: 2026-04-29
status: draft
related_task: E5-CAPI-001
tags: [capi, tablet, procurement, e5, field-distribution]
---

# Draft Email — CAPI Tablet Specifications for Procurement

**To:** Ma'am Juvy
**From:** Carl Patrick L. Reyes <clreyes6@up.edu.ph>
**Subject:** CAPI Tablet Specifications — ASPSI | DOH UHC Survey 2

---

Ma'am Juvy,

Good morning po. Below are the tablet specifications for the CAPI fieldwork. These tablets will run the CSEntry Android app for F1 (Facility Head), F3 (Patient Exit), and F4 (Community), with offline data capture, GPS auto-tagging, and one verification photo per case. The same tablet should also be capable of running the F2 HCW PWA via Chrome in case interviewer-administered fallback is needed.

## Minimum specifications (per unit)

- **Form factor:** Android tablet, 10-inch screen (8" acceptable but not preferred — F1/F3/F4 forms are dense)
- **OS:** Android 12 or higher (with active security updates)
- **RAM:** 4 GB minimum (6 GB or higher recommended)
- **Storage:** 64 GB internal minimum
- **Battery:** 6,000 mAh minimum — a full survey day is ~8 hours of active use
- **Connectivity:** Wi-Fi required; LTE/4G with SIM slot recommended for sync away from facility Wi-Fi
- **GPS:** Built-in GNSS (required for auto-coordinate capture per case)
- **Camera:** Rear camera, 5 MP or higher (required for verification photo per case)
- **Browser:** Latest Chrome with Service Worker + IndexedDB support (required for F2 PWA)
- **Touch:** Capacitive, 10-point multi-touch

## Suggested models with indicative price range

Good price-performance for PH field surveys — for reference, not exhaustive. Prices are SRP estimates as of Q2 2026; please confirm against current vendor quotes:

- Samsung Galaxy Tab A9+ (11", 4/64 GB, LTE) — **₱14,000 – ₱17,000**
- Samsung Galaxy Tab A8 (10.5", 4/64 GB) — **₱11,000 – ₱14,000**
- Lenovo Tab M10 Plus, 3rd Gen (10.6", 4/64 GB) — **₱12,000 – ₱15,000**
- Honor Pad X9 (11.5", 4/128 GB) — **₱11,000 – ₱13,000**

## Required accessories per tablet (with indicative price range)

- Rugged carrying case with hand strap — **₱500 – ₱1,500**
- Tempered-glass screen protector — **₱200 – ₱500**
- 20W or higher fast charger + USB-C cable — **₱500 – ₱1,000** (often bundled; spec a spare set per unit)
- 64 GB microSD card, optional buffer for photo overflow — **₱400 – ₱700**

**Indicative total per unit (tablet + accessories):** ~₱13,000 – ₱20,000 depending on model and bundle. Add ~10–15% on top for the spare-ratio units.

## Procurement notes

- Please include a ~10–15% spare ratio over the enumerator headcount for field replacements and damaged-unit quarantine.
- Units should ship with default Google Play Services. We will install CSEntry, the F1/F3/F4 dictionaries, and security baseline during imaging (covered under E5-CAPI-003).
- If LTE-capable, no SIMs are needed at procurement — we can provision those separately.

Happy to vet a vendor short-list before purchase, or clarify any line item.

Thank you po,
Carl
