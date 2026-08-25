# Block-NEST-K completion audit

Audit date: 2026-08-25. Outcome: **bounded null; engineering-only merge**.

The research protocol was sequential and fail-closed. Later development and
untouched gates were conditional on passing the synthetic mechanism gate. They
were not opened after the candidate failed its preregistered effect and runtime
thresholds.

| Requirement | Authoritative evidence | Decision |
|---|---|---|
| Scalable sparse initialization | `selib/seopt.py`; regression at 3,002 vertices; PR #11 | Pass; merged |
| Multi-view initialization | topology/feature/fused starts in `run_block_nest_synthetic.py` | Implemented and ablated |
| Exact block delta | theory derivation; 100K random and 184,560 exhaustive artifacts | Pass |
| Block fixed-K / monotonicity / termination | `BLOCK_NEST_K_THEORY.md`; fail-closed certificates | Pass |
| Exact pairwise merge-split | full objective reconstruction, restricted exact moves, theory boundary, tests | Pass as prototype |
| Node-local versus block-local separation | 10-node witness artifact, delta `-0.0738726643` | Pass |
| Repository regression safety | remote research suite: 32 passed, 1 skipped | Pass |
| Synthetic mechanism gate | K=6 12-cell screen plus K=3 five-seed fragmentation screen | Fail |
| Independent block effect | 0/12 K=6 cells improved over view-diverse node search; 0/12 selected restarts accepted a block | Fail |
| Merge-split effect | approximately 0.003% H2 improvement in positive pilots; inconsistent NMI/ARI | Fail `<0.5%` gate |
| Wall-clock gate | approximately 4.5–6.1x SparseInit in merge-split pilots | Fail `<3x` gate |
| Full five-dataset development | Conditional on synthetic pass | Not opened by protocol |
| Untouched confirmation | Conditional on development pass and algorithm freeze | Not opened; labels remain unqueried |
| Full external baseline campaign | Conditional on method survival | Not opened; avoids spending compute on a failed candidate |
| 100K–1M block scalability | Conditional on effect and `<3x` pilot | Not opened; prototype already failed runtime gate |
| Validated SELib correction merge | PR #11, main merge commit `68ab285711e473bedc6a9e1e54013fb156927aff` | Complete |
| Public null report | issue #10 comment `issuecomment-5412946446`; status/theory/evidence branch | Complete |
| New method / SOTA / paper claim | Gates failed | Explicitly rejected |

## Artifact integrity

- `block_delta_100k_seed20260825.json`:
  `d9e53200fb2aab0e9ee8393106ad454ed89300605c5cd9c520f34dbc4f80a47d`
- `block_delta_exhaustive_n10.json`:
  `6818932a2504075f45515db3bbfc29491b6b73ceef279a095cfa55d8b9ba76dc`
- `block_escape_witness_seed20260825.json`:
  `3a1654585c80e0b9d40b4a317dd1666475e013322a63c0e2308c8ea45318d864`
- five-seed conflict/fragmentation screen:
  `a980d132ebc515a2ffe38207dd850f5da776c2d937f4c82dd3ebd4bd96bcb5fd`

## Final boundary

Block moves are a mathematically valid, strictly stronger local neighborhood;
the tested proposal family is not an empirically supported new optimizer. The
only mainline changes are the sparse spectral and zero-volume fixed-K fixes.
Any predictive-MDL or Pareto view-ambiguity method is a new research objective,
not an uncompleted part of Block-NEST-K and must receive its own preregistration.
