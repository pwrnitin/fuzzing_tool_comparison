#!/bin/bash
# run_phase2.sh — Run the full Phase 2 multi-budget benchmark for Fuzzgoat.
# 3 tools × 3 budgets × 3 replications = 27 sequential runs (~6 hours).
# Resumable: skips already-completed configs in the CSV.

set -uo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
cd "$PROJECT_ROOT"

CSV="results/master_all_targets.csv"
OUTPUT_ROOT="runs/phase2"
PY="python3 scripts/run_one_fuzzgoat.py"

export PATH="$PATH:/home/pawarn/honggfuzz/hfuzz_cc:/home/pawarn/honggfuzz"

BUDGETS=(60 300 1800)
TOOLS=(lf afl hfuzz)
SEEDS=(1 2 3)

TOTAL=$(( ${#BUDGETS[@]} * ${#TOOLS[@]} * ${#SEEDS[@]} ))
DONE_COUNT=0
SKIPPED=0
RUN_COUNT=0

echo "============================================================"
echo "Phase 2 launcher — $TOTAL total configurations"
echo "Start: $(date)"
echo "============================================================"

for budget in "${BUDGETS[@]}"; do
    for tool in "${TOOLS[@]}"; do
        for seed in "${SEEDS[@]}"; do
            DONE_COUNT=$((DONE_COUNT + 1))

            if [ -f "$CSV" ] && \
               awk -F, -v t="$tool" -v b="$budget" -v s="$seed" \
                   'NR>1 && $1==t && $3==b && $4==s {found=1} END{exit !found}' \
                   "$CSV" 2>/dev/null; then
                echo "[$DONE_COUNT/$TOTAL] SKIP (already in CSV): tool=$tool budget=${budget}s seed=$seed"
                SKIPPED=$((SKIPPED + 1))
                continue
            fi

            echo ""
            echo "[$DONE_COUNT/$TOTAL] RUNNING: tool=$tool budget=${budget}s seed=$seed"
            echo "Started at: $(date +%H:%M:%S)"

            $PY --tool "$tool" --budget "$budget" --seed "$seed" \
                --output-root "$OUTPUT_ROOT" --csv "$CSV"

            RUN_COUNT=$((RUN_COUNT + 1))
        done
    done
done

echo ""
echo "============================================================"
echo "Phase 2 complete. End: $(date)"
echo "  ran:     $RUN_COUNT new configurations"
echo "  skipped: $SKIPPED already-complete configurations"
echo "  total:   $DONE_COUNT"
echo "  results: $CSV"
echo "============================================================"
