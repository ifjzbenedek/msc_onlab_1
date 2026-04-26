#!/bin/bash
#SBATCH --job-name=llm-compare
#SBATCH --partition=gpu
#SBATCH --qos=hallgato_qos
#SBATCH --gres=gpu:rtx3090:2
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --mem=16G
#SBATCH --time=12:00:00
#SBATCH --output=results/slurm_compare_%j.out

# ── Configuration (override via environment when submitting) ──
# Example: WRITER_MODEL=qwen3:32b sbatch slurm/compare.sh
WRITER_MODEL="${WRITER_MODEL:-qwen2.5-coder:14b}"
REVIEWER_MODEL="${REVIEWER_MODEL:-gemma2:9b}"
EASY="${EASY:-10}"
MEDIUM="${MEDIUM:-10}"
HARD="${HARD:-10}"
SEED="${SEED:-42}"
MAX_ITER="${MAX_ITER:-3}"
LANG="${LANG:-python3}"
ONLY_PIPELINES="${ONLY_PIPELINES:-}"
WM_BETA="${WM_BETA:-}"
WM_POOL="${WM_POOL:-}"
ENSEMBLE_POOL="${ENSEMBLE_POOL:-}"
WMR_BETA="${WMR_BETA:-}"
WMR_RETRY_BETA="${WMR_RETRY_BETA:-}"
EXP3_GAMMA="${EXP3_GAMMA:-}"

# ── Setup ──
cd "$HOME/msc_onlab_1" || exit 1
source .venv/bin/activate
export OLLAMA_HOST="http://localhost:11434"
mkdir -p results

# ── Start Ollama inside the job so SLURM can reclaim its GPU on exit ──
echo "Starting Ollama server..."
ollama serve > /tmp/ollama_${SLURM_JOB_ID}.log 2>&1 &
OLLAMA_PID=$!

VRAM_CSV="results/vram_${SLURM_JOB_ID}.csv"
bash slurm/vram_log.sh "$VRAM_CSV" 2 &
VRAM_PID=$!

trap "kill $OLLAMA_PID $VRAM_PID 2>/dev/null" EXIT
for i in $(seq 1 30); do
    if curl -s http://localhost:11434/api/tags > /dev/null; then
        echo "Ollama ready (pid=$OLLAMA_PID), VRAM logger pid=$VRAM_PID"
        break
    fi
    sleep 1
done

echo "Job $SLURM_JOB_ID started at $(date)"
echo "Node: $HOSTNAME"
echo "Writer: $WRITER_MODEL | Reviewer: $REVIEWER_MODEL"
echo "Problems: Easy=$EASY Medium=$MEDIUM Hard=$HARD"
echo "=========================================="

EXTRA_ARGS=()
if [ -n "$ONLY_PIPELINES" ]; then
    EXTRA_ARGS+=(--only-pipelines "$ONLY_PIPELINES")
fi
if [ -n "$WM_BETA" ]; then
    EXTRA_ARGS+=(--weighted-majority-beta "$WM_BETA")
fi
if [ -n "$WM_POOL" ]; then
    EXTRA_ARGS+=(--weighted-majority-pool "$WM_POOL")
fi
if [ -n "$ENSEMBLE_POOL" ]; then
    EXTRA_ARGS+=(--ensemble-pool "$ENSEMBLE_POOL")
fi
if [ -n "$WMR_BETA" ]; then
    EXTRA_ARGS+=(--wmr-beta "$WMR_BETA")
fi
if [ -n "$WMR_RETRY_BETA" ]; then
    EXTRA_ARGS+=(--wmr-retry-beta "$WMR_RETRY_BETA")
fi
if [ -n "$EXP3_GAMMA" ]; then
    EXTRA_ARGS+=(--exp3-gamma "$EXP3_GAMMA")
fi

python3 scripts/compare_methods.py \
    --writer-model "$WRITER_MODEL" \
    --reviewer-model "$REVIEWER_MODEL" \
    --easy "$EASY" \
    --medium "$MEDIUM" \
    --hard "$HARD" \
    --seed "$SEED" \
    --max-iterations "$MAX_ITER" \
    --lang "$LANG" \
    "${EXTRA_ARGS[@]}"

echo "=========================================="
echo "Job finished at $(date)"
