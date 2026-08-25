# Block-NEST-K preregistered paper gate

Working title: **Block-NEST-K: Certified Basin-Escaping Optimization for
Fixed-K Structural Entropy on Fragmented Attributed Graphs**.

This is a fail-closed plan. Dataset labels may be used only for final reporting,
never for restart selection, proposal acceptance, stopping, or hyperparameter
choice. Exact fused two-dimensional structural entropy is the sole optimizer and
restart-selection criterion.

## Frozen method candidate

1. Generate sparse spectral starts from topology, feature-kNN, and equal-mass
   fused views, plus feature K-means and seeded random controls.
2. Refine each start with exact fixed-K singleton moves.
3. Evaluate a fixed proposal family: topology components,
   cross-view-agreement blocks, and matched random control blocks.
4. Accept a block only when its exact fused-objective delta is below `-1e-12`.
5. Alternate singleton and block passes to a joint no-improvement certificate.
6. Add merge-split only after its exact-K rule is separately frozen and tested.

Proposal order, ties, tolerances, passes, feature 10-NN, mass normalization,
seeds, source commit, environment, and gates must be frozen before confirmation.

## Gate 1: theory and implementation

- Exact block delta, monotonicity, termination, fixed-K preservation,
  local-dominance statement, and incremental complexity.
- Exhaustive small weighted graphs through `n <= 10` where feasible.
- At least 100,000 random weighted block moves with error below `1e-12`.
- A node-local but block-improvable witness.

## Gate 2: synthetic mechanism study

- Sizes: `1K, 5K, 20K, 100K`; `K = 3, 6, 12`.
- Topology/feature signal: weak, medium, strong.
- Alignment: aligned, topology-only, feature-only, conflict.
- Fragmentation: `0%, 25%, 50%, 75%`.
- Degree: homogeneous and power-law; balance: balanced, moderate, severe.
- Pass: lower H2 than SparseInit-NEST in at least 80% of fragmented cells,
  with no false task-accuracy claim under null conditions.

## Gate 3: exposed development datasets

Datasets: Cora, Citeseer, ACM, DBLP, Amazon-Photo. Add components in this fixed
ablation order: sparse initialization, view diversity, singleton moves,
topology-component blocks, agreement blocks, merge-split.

Pass only if exact H2 improves on at least four of five; both NMI and ARI improve
on Citeseer and DBLP; ACM and Amazon-Photo regress by no more than `0.02`; and
end-to-end wall time remains below `3x` SparseInit-NEST.

## Gate 4: untouched confirmation

After freezing, run five seeds on PubMed, Amazon-Computers, Coauthor-CS,
Coauthor-Physics, and WikiCS. Labels remain sealed until every seed artifact,
hash, fixed-K check, objective reconstruction, and runtime record passes.

Pass only if H2 is no worse on all five and lower on at least four; mean NMI and
ARI ranks improve; at most one dataset regresses by more than `0.02`; a paired
bootstrap interval for H2 improvement excludes zero; and wall time is `<3x`.

## Baselines and ablations

Internal: feature K-means, topology spectral, fused sparse spectral, fixed-K
greedy modularity, CoDeSEG-compatible optimization, frozen NEST,
SparseInit-NEST, and Block-NEST-K. External attributed methods: DGI, SSGC,
DAEGC, DMoN, DeSE, and LSEnet. RAGC is admissible only under a complete
label-isolated protocol.

Required ablations: random versus sparse spectral; single versus view-diverse;
singleton versus block; remove topology blocks; remove agreement blocks; remove
merge-split; matched random blocks; oracle-NMI and truth-warm diagnostics clearly
marked non-comparable.

## Downgrade/stop conditions

Do not form a method paper if sparse initialization explains essentially all
gains, block moves reduce H2 by less than roughly 0.5%, untouched NMI/ARI
regress, dataset-specific weights are required, or matched random blocks perform
equally. Instead, merge only validated infrastructure into SELib and report the
bounded null finding.
