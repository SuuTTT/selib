# TAMC 2026 submission-readiness record

Status: **UPLOAD-READY REVIEW PDF**.

## Official requirements

- Official page: <https://www.cs.sdu.edu.cn/tamc2026.htm>
- Deadline date: 10 August 2026 (the public page gives no cutoff time zone).
- Review: double-blind.
- Format: Springer LNCS, unmodified margins and font size, A4.
- Limit: 12 pages including references; optional appendix excluded.
- Original work; no simultaneous submission of essentially the same results.

## Authoritative upload artifacts

- Source: `paper/se-hier-nni/main.tex`
- Main build: `latexmk -cd -pdf -interaction=nonstopmode -halt-on-error paper/se-hier-nni/main.tex`
- Combined build: run the same command on `paper/se-hier-nni/main-with-appendix.tex`.
- Upload PDF: `paper/se-hier-nni/main-with-appendix.pdf` when EasyChair accepts
  the optional appendix in the same file; its first 12 pages are the complete
  main paper and references, and page 13 begins the proof appendix. EasyChair
  exposes one PDF slot, so this combined artifact is the authoritative upload.
- Ready-to-upload copy: `output/submission/TAMC2026_NEST/NEST_TAMC2026_anonymous_with_appendix.pdf`.
- Complete local package: `output/submission/NEST_TAMC2026_submission_package.zip`.
- Checker-only/main artifact: `paper/se-hier-nni/main.pdf` (12 pages).
- Branch: `codex/se-hier-nni-paper`
- Format result: 12 A4 pages; all fonts embedded; no Type 3 fonts.
- TAMC checker: pass in `--double-blind` mode with zero mechanical failures.
- Visual inspection: all 12 main pages and the optional proof page rendered;
  changed tables, references, headers, and page breaks inspected.
- Science gate: `ADVERSARIAL_REVIEW.md` passes the manuscript to submission.
- Evidence: the scaled verifier passes seven completed hash-sealed blocks:
  500 main graphs and exact audits at n=14 and n=16. Together with the sealed
  n=12 audit, NEST reaches 370/375 exact optima. The incomplete unsealed exact12
  checkpoint is excluded. Existing code tests: 19 pass and 1 is skipped.

The SHA-256 value is frozen in `ARTIFACT_MANIFEST.md` after the final build.

## Accepted-paper layout calibration

- Exemplar: Sunny Atalig and Marek Chrobak, *A Tight Threshold Bound for Search
  Trees with 2-Way Comparisons*, TAMC 2024, LNCS 14637, pp. 99--110.
- The published exemplar has 12 pages including references and no appendix.
- Its publisher-trimmed page size is not the submission template. This review
  PDF keeps the officially required A4 `llncs` layout without changing margins
  or font size.
- The NEST main paper follows the same 12-page main-plus-references boundary.
  The permitted appendix follows that boundary in the same EasyChair PDF.

## Human attestations at upload

These are EasyChair/account facts rather than missing paper content:

- [ ] Enter the complete author list and choose a corresponding author.
- [ ] Confirm that the Local-Traps/clique draft is not simultaneously under
      review with essentially the same NNI identity or results.
- [ ] Decide whether all authors qualify for the best-student-paper award.
- [ ] Submit before the unspecified cutoff; do not assume 23:59 AoE.
- [ ] Download the uploaded PDF and verify its SHA-256 against the manifest.
- [ ] Record the EasyChair submission ID and server timestamp.

No author identity should be added to the review PDF.
