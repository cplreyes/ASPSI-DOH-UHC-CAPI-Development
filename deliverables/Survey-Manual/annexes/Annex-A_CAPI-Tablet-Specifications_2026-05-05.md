# Annex A — CAPI Tablet Specifications

**Audience:** ASPSI Procurement, Field Operations
**Status:** Original sent to ASPSI procurement on 2026-04-29; this annex version is the same content reformatted for inclusion with the Survey Manual.

---

## Purpose

These specifications govern the Android tablets to be procured for the UHC Year 2 CAPI fieldwork. The same tablet supports F1 (Facility Head), F3 (Patient), F4 (Household), and F0 (Supervisor) applications running under CSEntry, plus the F2 HCW PWA via Chrome where interviewer-administered fallback is required.

## Minimum specifications (per unit)

| Spec | Requirement |
|---|---|
| Form factor | Android tablet, 10-inch screen (8" acceptable but not preferred — F1/F3/F4 forms are dense) |
| OS | Android 12 or higher with active security updates |
| RAM | 4 GB minimum (6 GB or higher recommended) |
| Storage | 64 GB internal minimum |
| Battery | 6,000 mAh minimum (a full survey day is ~8 hours of active use) |
| Connectivity | Wi-Fi required; LTE/4G with SIM slot recommended for sync away from facility Wi-Fi |
| GPS | Built-in GNSS (required for auto-coordinate capture per case) |
| Camera | Rear camera, 5 MP or higher (required for verification photo per case) |
| Browser | Latest Chrome with Service Worker + IndexedDB support (required for F2 PWA) |
| Touch | Capacitive, 10-point multi-touch |

## Suggested models — indicative pricing as of Q2 2026

### Recommended tier (₱13,000 – ₱20,000/unit incl. accessories)

- Samsung Galaxy Tab A9+ (11", 4/64 GB, LTE)
- Samsung Galaxy Tab A8 (10.5", 4/64 GB)
- Lenovo Tab M10 Plus, 3rd Gen (10.6", 4/64 GB)
- Honor Pad X9 (11.5", 4/128 GB)

### Affordable tier (₱9,500 – ₱14,000/unit)

Still meets minimum spec but **confirm GPS is included** before ordering — some Wi-Fi-only budget SKUs drop the GNSS chip:

- Lenovo Tab M9, 3rd Gen (9", 4/64 GB)
- Honor Pad X8a (11.5", 4/128 GB, LTE variant for GPS)
- Xiaomi Redmi Pad SE 8.7" LTE (4/128 GB, Android 14)
- Refurbished Samsung Galaxy Tab A8 (require warranty + battery-health check)

### Modest tier (₱7,000 – ₱12,000/unit)

Bare-minimum-but-functional. Specify the **LTE variant** for GNSS:

- Samsung Galaxy Tab A7 Lite LTE (8.7", 3/32 GB, Android 11→12)
- Lenovo Tab M8, 4th Gen LTE (8", 3/32 or 4/64 GB, Android 12)
- Realme Pad Mini LTE (8.7", 3/32 or 4/64 GB)

> Trade-offs at this tier: 8" screen makes F1/F3/F4 dense grids harder to tap (train enumerators to landscape); 3 GB RAM is OK for CSEntry alone but sluggish if F2 PWA fallback is needed; 32 GB storage requires regular sync-and-purge discipline; confirm security-update window of 12–18 months.

> Going below ~₱5,500/unit usually means dropping below minimum spec. Avoid no-name brands (Teclast, Blackview, Doogee, etc.) — build quality and security-update support are not viable for a multi-month engagement.

## Required accessories per tablet

| Item | Indicative price |
|---|---|
| Rugged carrying case with hand strap | ₱500 – ₱1,500 |
| Tempered-glass screen protector | ₱200 – ₱500 |
| 20 W+ fast charger + USB-C cable (one spare per unit) | ₱500 – ₱1,000 |
| 64 GB microSD (optional photo overflow buffer) | ₱400 – ₱700 |

## Procurement notes

- Add **10–15% spare ratio** over enumerator headcount for field replacements and damaged-unit quarantine.
- Units ship with default Google Play Services. CSEntry, the CAPI applications, and security baseline are installed by the Data Programmer during imaging.
- If LTE-capable, SIMs are not needed at procurement — provisioned separately.
- Vendor short-lists are vetted by the Data Programmer before purchase.
