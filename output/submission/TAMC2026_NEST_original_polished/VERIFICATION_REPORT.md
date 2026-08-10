# NEST original-polished package verification

Status: **PASS** for the paper build, mechanical TAMC preflight, and seven
completed hash-sealed experimental blocks. The interrupted exact12 checkpoint
is excluded.

## Document checks

- Anonymous main paper: 12 A4 pages.
- Combined upload: 15 A4 pages (12-page paper plus three-page appendix).
- All fonts embedded; no Type 3 fonts.
- No undefined citations or references.
- No overfull boxes reported by the final LaTeX build.
- Title and abstract synchronized with `EASYCHAIR_FIELDS.txt`.

## 64-vertex benchmark

- 500 graph instances, 3,500 method records, and 500 manifests.
- Paired gain over the better of HCSE and BBM: 0.4239 +/- 0.0086 bits
  (95% paired t interval).
- Strict wins: 500/500.

## Exact-optimum audit

| n | Instances | NEST | HCSE | label-free BBM |
|---:|---:|---:|---:|---:|
| 12 | 250 | 249 | 2 | 1 |
| 14 | 100 | 99 | 0 | 0 |
| 16 | 25 | 22 | 0 | 0 |

Across the three completed size strata, NEST reaches 370/375 exact optima; its
exact 95% Clopper--Pearson interval is [96.92%, 99.57%].
