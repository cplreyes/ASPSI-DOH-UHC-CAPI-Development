# 1305 - F3 section order restored to the printed sequence

Tester reported the CAPI ran A,B,C,D then G,H then E,F. Carl ruled for the PRINTED order,
which means the Aug-17 paper's two "Note for CAPI Version" blocks (F3-extract.md L1237
and L1808), asking for outpatient/inpatient to be front-loaded ahead of primary-care
utilization, are deliberately NOT implemented. Registered as a divergence.

Shipped in F3 v6.0.0. Order is now A,B,C,D,E,F,G,H,I,J,K,L.

## What changed

generate_dcf.py   record order - build_section_e/f moved back ahead of build_section_g/h
generate_fmf.py   FORM_PLAN screen order - the E and F entries moved back ahead of G
generate_apc.py   the four skip retargets the front-load had required, reverted:
                    Q51_OTHER_INSURANCE = 2   Q88_WHY_VISIT  -> Q53_HAS_PCP
                    AREA_HAS_BUCAS = 2        Q53_HAS_PCP    -> Q116_NBB_HEARD
                    Q99_BUCAS_HEARD = 2       Q53_HAS_PCP    -> Q116_NBB_HEARD
                    Q1142_HAS_OTHER = 2       Q53_HAS_PCP    -> Q116_NBB_HEARD
                    PROC Q105_REASON gate     Q53_HAS_PCP    -> Q116_NBB_HEARD
                  PROC Q88_WHY_VISIT gate unchanged (G is still followed by H).

Every target reverts to a value the front-load commit had recorded, so this is a
documented reversal rather than a fresh routing guess. The Q51 revert also restores
agreement with the paper's own printed note, which reads "IF No GOTO proceed to Q53".

## Verification

verify_questions F3 375/375 reachable, 0 dead-conditions, 0 bad-skips, PASS
preflight ALL CLEAN - csentry_verify PASS - Designer compile Successful 13:41:58
fmf first-appearance order A,B,C,D,E,F,G,H,I,J,K,L
apc emits exactly: 1 skip to Q53_HAS_PCP, 1 skip to Q105_REASON, 4 skip to Q116_NBB_HEARD
served package 12 entries / 8 PSGC / v6.0.0 x8; Q88 tick-list from v5.0.0 still intact

## Data shape

Moving records is a MAJOR change and old .csdb files are not compatible - hence v6.0.0
one hour after v5.0.0. No collected data is affected: no F3 case has been created or
modified on CSWeb since 2026-07-27 (verified against cspro_sync_history).

## Evidence

F3-v6.0.0-section-order.png - itel P10001L, sideloaded from the SERVED package, section
navigator showing A / Patient Type / FC Geo / B / C / D / E / F / G...
