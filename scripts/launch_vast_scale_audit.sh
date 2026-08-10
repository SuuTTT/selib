#!/usr/bin/env bash
set -euo pipefail

# Low-priority, resumable CPU audit for an already-running Vast worker.
# The caller is responsible for confirming that cores 0--7 and at least 8 GiB
# of RAM are idle.  Every process is single-core, memory-capped, and bounded.

REPO=${REPO:-/workspace/nest-scale-20260810}
RUN_ID=${RUN_ID:-scale-audit-20260810}
SESSION=${SESSION:-nest-scale-audit}
RUN_ROOT="$REPO/results/$RUN_ID"
LOG_ROOT="$REPO/logs/$RUN_ID"
PYTHON="$REPO/.venv/bin/python"

mkdir -p "$RUN_ROOT" "$LOG_ROOT"
if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session already exists: $SESSION" >&2
  exit 2
fi

export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1

launch_window() {
  local window=$1
  local core=$2
  shift 2
  local command=$*
  local wrapped
  printf -v wrapped \
    'cd %q; set -o pipefail; export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1; nice -n 15 ionice -c3 taskset -c %q prlimit --as=8589934592 timeout 12h %s > %q 2>&1; rc=$?; echo "$rc" > %q; if [ "$rc" -eq 0 ]; then sha256sum %q > %q; fi; exit "$rc"' \
    "$REPO" "$core" "$command" "$LOG_ROOT/$window.log" \
    "$RUN_ROOT/$window.status" "$RUN_ROOT/$window.json" \
    "$RUN_ROOT/$window.sha256"

  if ! tmux has-session -t "$SESSION" 2>/dev/null; then
    tmux new-session -d -s "$SESSION" -n "$window" "bash -lc $(printf %q "$wrapped")"
  else
    tmux new-window -d -t "$SESSION" -n "$window" "bash -lc $(printf %q "$wrapped")"
  fi
}

for spec in \
  'n64-clean:0:clean' \
  'n64-noisy:1:noisy' \
  'n64-imbalanced:2:imbalanced' \
  'n64-weighted:3:weighted' \
  'n64-weak:4:weak-hierarchy'
do
  IFS=: read -r window core regime <<<"$spec"
  launch_window "$window" "$core" \
    "$PYTHON scripts/run_nni_benchmark.py --seed-start 1000 --seeds 100 --regimes $regime --output $RUN_ROOT/$window.json --resume"
done

launch_window exact12 5 \
  "$PYTHON scripts/run_nni_restart_fairness.py --seed-start 2000 --seeds 200 --budget 32 --campaign-seed 20260811 --max-nodes 12 --output $RUN_ROOT/exact12.json --resume"

launch_window exact14 6 \
  "$PYTHON scripts/run_nni_restart_fairness.py --seed-start 3000 --seeds 20 --budget 32 --campaign-seed 20260812 --target-n 14 --max-nodes 14 --output $RUN_ROOT/exact14.json --resume"

launch_window exact16 7 \
  "$PYTHON scripts/run_nni_restart_fairness.py --seed-start 4000 --seeds 5 --budget 32 --campaign-seed 20260813 --target-n 16 --max-nodes 16 --output $RUN_ROOT/exact16.json --resume"

echo "launched tmux session: $SESSION"
echo "results: $RUN_ROOT"
echo "logs: $LOG_ROOT"
