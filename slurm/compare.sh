#!/bin/bash
#SBATCH --job-name=llm-compare
#SBATCH --partition=gpu
#SBATCH --qos=hallgato_qos
#SBATCH --gres=gpu:rtx3090:2
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --mem=16G
#SBATCH --time=06:00:00
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

# ── Setup ──
cd "$HOME/msc_onlab_1" || exit 1
source .venv/bin/activate
export OLLAMA_HOST="http://localhost:11434"
mkdir -p results

echo "Job $SLURM_JOB_ID started at $(date)"
echo "Node: $HOSTNAME"
echo "Writer: $WRITER_MODEL | Reviewer: $REVIEWER_MODEL"
echo "Problems: Easy=$EASY Medium=$MEDIUM Hard=$HARD"
echo "=========================================="

python3 scripts/compare_methods.py \
    --writer-model "$WRITER_MODEL" \
    --reviewer-model "$REVIEWER_MODEL" \
    --easy "$EASY" \
    --medium "$MEDIUM" \
    --hard "$HARD" \
    --seed "$SEED" \
    --max-iterations "$MAX_ITER" \
    --lang "$LANG"

echo "=========================================="
echo "Job finished at $(date)"
