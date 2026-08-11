# NEST-G / TCS Journal Paper Handoff

Last updated: 2026-08-12 (Asia/Shanghai)

This is the operational source of truth for the next agent. Read it completely before editing code, results, or the manuscript. The immediate objective is to turn the current first journal draft into a defensible, submission-ready *Theoretical Computer Science* paper without contaminating the frozen confirmatory experiment.

## 1. Project identity and goal

- Project: NEST-G, the journal extension of the submitted TAMC NEST paper.
- Repository: [SuuTTT/selib](https://github.com/SuuTTT/selib)
- Local checkout: `/Users/suu/Documents/codexcli/selib-nni-paper`
- Working branch: `codex/nest-entropy-grafting`
- Current local manuscript commit before this handoff: `6713a98` (`Draft TCS extension with certified graft search`)
- Intended venue: *Theoretical Computer Science* (TCS), preferably the “Algorithms, automata, complexity and games” section, subject to a final scope check.
- Final goal: a submission-ready journal paper with a correct theorem spine, a verified graft-search experiment, complete human metadata and declarations, a clean PDF, and a reproducible source package.

The central journal story is:

1. a constrained structural-entropy hierarchy problem is computationally hard;
2. rooted NNI and subtree grafting admit exact, efficiently checkable entropy changes;
3. grafting strictly enlarges the NNI neighborhood and provides a stronger local-optimality certificate;
4. the resulting NEST-G search is evaluated under a frozen, disjoint confirmatory protocol.

## 2. Current paper artifacts

- LaTeX source: `paper/se-hier-nni-tcs/main.tex`
- Bibliography: `paper/se-hier-nni-tcs/references.bib`
- Current candidate PDF: `output/pdf/NEST_TCS_journal_candidate_v0.2_2026-08-11.pdf`
- Current source archive: `output/submission/NEST_TCS_journal_candidate_v0.2_2026-08-11-source.tar.gz`
- Current hash manifest: `output/submission/NEST_TCS_journal_candidate_v0.2_2026-08-11-SHA256.txt`
- Conference-to-journal delta: `paper/se-hier-nni-tcs/CONFERENCE_TO_JOURNAL_DELTA.md`
- Claim/proof ledger: `paper/se-hier-nni-tcs/CLAIM_PROOF_LEDGER.md`
- Submission gap report: `paper/se-hier-nni-tcs/SUBMISSION_GAP_REPORT.md`
- Human metadata checklist: `paper/se-hier-nni-tcs/HUMAN_METADATA_AND_DECLARATIONS.md`
- Highlights: `paper/se-hier-nni-tcs/HIGHLIGHTS.txt`
- Build instructions: `paper/se-hier-nni-tcs/BUILD.md`

Current candidate checks already passed:

- 19 pages;
- 191-word abstract;
- 6 keywords and 4 highlights;
- all fonts embedded;
- no undefined citations or references;
- no overfull boxes;
- all pages visually inspected;
- fixed-date source archive rebuilt bit-identically.

Recorded SHA-256 values:

```text
PDF     6c28725e22924813d365711c00bd0daf1aab23041e4ba402ee40d91d247fd0a8
archive f1321c720bbee98337ecade8bc853be5a6319e825d61d377b2e2669c200fae83
```

These hashes describe the v0.2 candidate only. Regenerate and record new hashes after any manuscript change.

## 3. What is already established

### 3.1 Theory currently in the draft

The draft states and proves the following scoped results:

- The balanced two-module structural-entropy decision problem is NP-complete on simple unweighted cubic graphs through an exact affine equivalence to Minimum Bisection.
- The weighted rooted-NNI entropy change has an exact local formula.
- A subtree graft has an exact edge-LCA delta formula.
- The same graft delta has an exact changed-incidence/path-supported form.
- Every rooted NNI is a restricted legal graft, so the graft neighborhood contains the NNI neighborhood.
- Exhaustive NEST-G stopping certifies graft-local optimality and therefore one-NNI local optimality.
- The correctness-first reference sweep has complexity `O(n^2(n+|E|))`.

Do not broaden these claims without a new proof. In particular:

- the hardness theorem is for the constrained balanced height-two problem, not unrestricted 2D structural entropy or the full encoding-tree problem;
- a graft-local certificate is not a proof of global optimality;
- no general approximation ratio has been proved;
- a round-limited implementation is only certified when it stops because no improving graft remains, not merely because the round cap is reached.

### 3.2 Verified graft evidence

`results/tcs_graft_reference_validation.json` contains:

- 1,680 independently rescored graft moves;
- maximum edge-LCA delta error: `1.4016565685892601e-15`;
- maximum changed-path delta error: `1.3322676295501878e-15`;
- 4 end-to-end graft-local search checks.

`results/tcs_graft_exact_miss_diagnostic.json` contains:

- `exact_before = 0`;
- `exact_after_graft = 5`;
- all 5 previously missed exact instances repaired;
- elapsed time about 64.9 seconds.

The 5/5 result is a diagnostic result, not an unbiased performance estimate: those five cases were selected because the earlier NEST method missed them. It supports the strict-neighborhood mechanism and motivates the disjoint confirmatory suite.

### 3.3 Inherited TAMC evidence

The frozen TAMC audit is under `results/scale-audit-20260810/`:

- 500 graphs with 64 vertices across five hierarchical regimes;
- NEST beat the stronger of HCSE and BBM on all 500 paired graphs;
- on 375 exact small instances, NEST reached the exact optimum on 370;
- corresponding exact hits were 2/375 for HCSE and 1/375 for BBM.

These results motivate the journal extension but do not substitute for a disjoint NEST-versus-NEST-G confirmation.

## 4. Frozen confirmatory experiment — integrity-critical

The next empirical task is already frozen.

- Protocol: `results/tcs_graft_confirmatory_protocol.json`
- Runner: `scripts/run_tcs_graft_confirmation.py`
- Intended output: `results/tcs_graft_confirmatory_exact12.json`
- Protocol version: `tcs-nest-graft-confirmatory-v1`
- Freeze time: `2026-08-11T20:00:00+08:00`

Frozen design:

- `n = 12`;
- regimes: clean, noisy, imbalanced, weighted, weak-hierarchy;
- 20 graphs per regime, with regime-local graph seeds `[500, 520)`;
- 100 graphs total;
- 32 random pairwise-coalescent starts per graph;
- campaign seed `20260811`;
- baseline endpoint: exact one-NNI descent followed by bounded two-step search;
- two-step settings: at most 8 rounds, beam width 16, barrier 0.05 bits;
- NEST-G endpoint: exhaustive best-improvement full-rescore graft search, followed by NNI verification, at most 100 rounds;
- exact-optimum tolerances: absolute `1e-9`, relative `1e-8`;
- primary endpoints: paired exact-hit difference and paired entropy improvement;
- falsifier: do not claim general empirical superiority if NEST-G fails to improve either exact-hit rate or entropy on this disjoint suite.

Frozen source hashes:

```text
scripts/run_tcs_graft_confirmation.py
6bda24b6a8ebb82abde3536e648c2bcd3cda1eab23ec92d949fc459f0419ae72

selib/htree.py
0440d1d4b1040c67d408586e7a82fbddad3b9ea59aa17520c741b646d0d0b42b
```

### Do not contaminate this protocol

Before completing v1, do **not** edit either frozen source file. The runner checks their hashes and aborts on mismatch. If a change is genuinely necessary, create and freeze a clearly named v2 protocol before observing any new full-suite outcome. Never silently replace v1.

Do not tune parameters, seeds, regimes, or claims after inspecting outcomes. Do not use ground-truth labels to construct or choose a tree. The exact optimum is computed only after both method endpoints have been selected.

The runner is resumable and writes after each graph. Run only one process against a given output file. The present runner is serial; do not launch multiple workers writing the same output.

## 5. Immediate execution plan

### P0 — Clean smoke test

The local macOS environment under `~/Documents` has shown abnormal import/site-package stalls. Old stalled test processes were stopped, and no confirmatory outcome was observed. Prefer a clean Linux CPU environment.

Requirements:

- Python 3;
- NetworkX;
- NumPy;
- pytest for the regression test;
- no GPU and no paid API;
- approximately 4–8 CPU cores and 8 GB RAM is ample;
- an already-running idle CPU box is acceptable, but do not interrupt or renice existing jobs.

Suggested commands:

```bash
cd /path/to/selib
python3 -m venv .venv-tcs
.venv-tcs/bin/pip install networkx numpy pytest
.venv-tcs/bin/python -m pytest tests/test_nni.py -q
.venv-tcs/bin/python scripts/run_tcs_graft_confirmation.py \
  --protocol results/tcs_graft_confirmatory_protocol.json \
  --output /tmp/tcs-graft-smoke.json \
  --limit 1
```

For the smoke run, verify:

- frozen hashes pass;
- tests pass;
- exactly one graph record is produced;
- all numeric outcomes are finite;
- the job does not threaten memory, disk, or other workloads.

The smoke output is operational only and must not be mixed into the confirmatory result.

### P1 — Complete and verify the frozen 100-graph run

```bash
.venv-tcs/bin/python scripts/run_tcs_graft_confirmation.py \
  --protocol results/tcs_graft_confirmatory_protocol.json \
  --output results/tcs_graft_confirmatory_exact12.json
```

After completion, independently verify:

- protocol version and source hashes;
- exactly 100 distinct graph records;
- 20 records for each of the five regimes;
- declared seed ranges and no duplicates;
- 32 starts per graph;
- finite entropy, runtime, and count fields;
- local-certificate conditions at reported endpoints;
- exact-hit calculation uses the declared tolerances;
- output SHA-256 is recorded before manuscript editing.

Report at minimum:

- exact hits for baseline and NEST-G, with binomial confidence intervals;
- paired exact-hit difference, preferably with an exact paired test/McNemar analysis where applicable;
- mean and median paired entropy improvement;
- bootstrap or paired 95% confidence interval for the mean entropy improvement;
- number of strict wins, ties, and losses;
- runtime and evaluated-candidate counts;
- regime-wise breakdown, clearly marked secondary if the primary endpoint is pooled.

### P2 — Update the manuscript according to the result

If the frozen result is positive:

- add one compact confirmatory table comparing the baseline endpoint with NEST-G;
- put at most one or two headline numbers in the abstract;
- update the introduction contributions, experiment section, discussion, and conclusion;
- distinguish diagnostic 5/5 repair from disjoint confirmation;
- update `CLAIM_PROOF_LEDGER.md`, `CONFERENCE_TO_JOURNAL_DELTA.md`, and `SUBMISSION_GAP_REPORT.md`.

If the result is null or negative:

- do not make a general NEST-G superiority claim;
- preserve the exact graft calculus, neighborhood-containment theorem, stronger local certificate, and diagnostic strict-neighborhood example;
- report the frozen outcome honestly and decide whether the paper remains a theory/algorithm contribution or needs a predeclared second study.

Do not hide a failed frozen result or quietly change the protocol.

### P3 — Independent proof audit

Audit every proof line against the claim/proof ledger, especially:

- the exact source and statement of Minimum Bisection hardness on cubic graphs;
- NP membership and the handling of thresholds/rational comparison;
- the affine cut-to-entropy equivalence in the balanced height-two setting;
- the changed-incidence/path-support statement for graft moves;
- the precise NNI-as-graft mapping;
- the distinction between natural no-improvement stopping and a round cap;
- all complexity assumptions and data structures.

Any theorem correction must propagate to the abstract, introduction, theorem statement, proof, discussion, conclusion, highlights, and cover letter.

### P4 — Human-only metadata and policy decisions

The agent must not invent these. Ask the author to resolve:

- final author list and order;
- affiliations and postal addresses;
- corresponding author, email, and ORCID;
- whether the selected TCS workflow is anonymous;
- funding statement;
- conflict-of-interest statement;
- final generative-AI declaration;
- code/data archive and DOI;
- archival citation, status, copyright, and disclosure of the TAMC preliminary version.

Track answers in `paper/se-hier-nni-tcs/HUMAN_METADATA_AND_DECLARATIONS.md`.

### P5 — Submission preflight and package

Use the fixed-date build:

```bash
cd /Users/suu/Documents/codexcli/selib-nni-paper/paper/se-hier-nni-tcs
SOURCE_DATE_EPOCH=1786449600 FORCE_SOURCE_DATE=1 \
  latexmk -gg -pdf -interaction=nonstopmode -halt-on-error main.tex
```

Then:

- check undefined references/citations and overfull boxes;
- render and visually inspect every page at readable resolution;
- verify tables, algorithms, equations, and figure labels do not collide or leave accidental blank regions;
- verify embedded fonts and PDF metadata;
- rebuild the source archive from tracked required files only;
- rebuild and verify the SHA-256 manifest;
- run the TCS journal audit skill described below;
- retain a versioned PDF rather than overwriting the last known-good candidate.

### P6 — Publication and branch handling

Do not merge or push merely because the local draft is complete. Obtain explicit user approval first. Remote agents cannot see the local commits until the branch is pushed or the repository is transferred.

## 6. TCS workflow skill

The local TCS journal skill is in a separate checkout:

- repository: `/Users/suu/Documents/codexcli/aaai-campaign-skills-tcs`
- branch: `codex/tcs-journal-pipeline`
- local commit: `ac62e81` (`Add TCS journal submission pipeline`)
- skill: `submission/tcs-journal-pipeline/SKILL.md`

Read that `SKILL.md` completely before using the workflow. Its custom audit currently passes the structural paper checks and flags only unresolved author metadata, conflict, and funding information.

Important: the checkout's `origin` points to the local `/Users/suu/Documents/codexcli/aaai-campaign-skills`, not directly to GitHub. The new skill commit has not been published to GitHub. It is available to another agent on this Mac but not automatically to a remote worker.

## 7. Version-control safety

The paper worktree currently contains unrelated or stale untracked files:

```text
output/.DS_Store
output/pdf/NEST_TCS_first_draft_2026-08-11.pdf
paper/.DS_Store
paper/se-hier-nni-tcs/main 2.pdf
paper/se-hier-nni-tcs/main.spl
paper/se-hier-nni/main-with-appendix.synctex.gz
paper/se-hier-nni/main.synctex.gz
tmp/
```

Do not delete, add, or overwrite these unless the user explicitly confirms their purpose. Stage only files intentionally changed for the journal paper. Never use destructive Git commands to clean the worktree.

Keep experimental results, protocol files, source hashes, statistical reports, and manuscript claims in the same evidence chain. Commit logical milestones separately.

## 8. Definition of done

The TCS paper is ready for the author’s final submission review only when:

- the frozen confirmation is completed and independently verified, or the manuscript is explicitly scoped so it makes no unsupported general empirical claim;
- all theorem and proof audits pass;
- every quantitative paper claim is traceable to a versioned result artifact;
- the conference-to-journal novelty is explicit and substantial;
- all human metadata and declarations are resolved;
- the PDF passes textual and visual preflight;
- the source archive rebuilds reproducibly and hashes are recorded;
- the user has approved any remote push, merge, or submission action.

## 9. Minimal pickup prompt for another agent

Copy the following prompt to the replacement agent:

```text
Take over the NEST-G TCS journal project at
/Users/suu/Documents/codexcli/selib-nni-paper on branch
codex/nest-entropy-grafting.

First read paper/se-hier-nni-tcs/HANDOFF.md completely, then read the TCS
workflow skill at /Users/suu/Documents/codexcli/aaai-campaign-skills-tcs/
submission/tcs-journal-pipeline/SKILL.md and the handoff's listed proof,
submission, and protocol documents.

Your goal is a defensible, submission-ready Theoretical Computer Science
journal paper. Start with P0: verify HEAD/status, verify the frozen source
hashes, run tests and a one-graph smoke test in a clean Linux CPU environment,
then run and independently validate the frozen 100-graph confirmation. Do not
edit the frozen runner or selib/htree.py, tune after seeing outcomes, use paid
APIs, disturb existing jobs, invent human metadata, delete untracked files, or
push/merge without explicit approval. Preserve the negative-result branch of
the plan and keep every numerical claim traceable to a result artifact.

Post a concise progress record after each P0–P6 milestone containing: commands,
commit/branch, artifact paths and hashes, checks passed, failures, resource use,
claim changes, and the next action.
```

## 10. First status message the new agent should send

Before running anything expensive, the next agent should report:

1. the observed branch, HEAD, and dirty files;
2. whether both frozen hashes match;
3. which clean CPU host/environment it will use;
4. the smoke-test command and expected artifacts;
5. confirmation that it will preserve the frozen protocol and the null/negative outcome path.
