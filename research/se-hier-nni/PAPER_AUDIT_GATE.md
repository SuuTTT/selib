# Paper audit gate

Audit date: 2026-08-10. Verdict: **PASS TO SUBMISSION**.

## Mechanical and policy gate

- Official TAMC 2026 page rechecked: review is double-blind.
- The PDF correctly uses anonymous author and affiliation fields.
- A4 Springer LNCS, 12 pages including references, no margin/font changes.
- No undefined citation/reference, overfull box, missing graphic, or Type 3 font.
- All 12 main pages plus the three-page optional appendix rendered; every
  changed appendix page and both new probability tables inspected.
- `audit_tamc_submission.py --double-blind` passes on the 12-page main artifact;
  the checker does not parse the CFP's excluded optional appendix.

## Scientific gate

- Exact delta proof independently re-expanded in `ADVERSARIAL_REVIEW.md`.
- Binary sufficiency is attributed to SuperTAD and HCSE and re-derived only for
  completeness. The SE-specific arbitrary-subset recurrence matches enumeration
  of all 105 rooted binary trees at n=5; generic cluster-trellis prior is cited.
- Zero-volume scope is now explicit in the theorem and preliminaries.
- Main and restart-optimum artifact verifiers pass.
- 19 automated tests pass; 1 optional-dependency test is skipped.
- The basin verifier checks exact topology/history totals, frozen exhaustive
  counts, all 80,000 Monte Carlo trials, confidence intervals, and restart
  probability transforms.
- Current primary-source novelty search found no prior exact discrete SE--NNI
  optimizer; closest-work boundaries are documented in `NOVELTY_AUDIT.md`.

## Human upload-only items

EasyChair still requires private author metadata, a corresponding author, and
a non-simultaneous-submission attestation. These are account/author facts, not
defects in the double-blind paper. See `SUBMISSION_READINESS.md`.

The earlier generic parser report was discarded because it did not follow
LaTeX `\input` files and incorrectly treated required anonymous fields as
named-author placeholders.
