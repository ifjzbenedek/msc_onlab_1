#!/bin/bash
#SBATCH --job-name=llm-explore
#SBATCH --partition=gpu
#SBATCH --qos=hallgato_qos
#SBATCH --gres=gpu:rtx3090:2
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --mem=16G
#SBATCH --time=12:00:00
#SBATCH --output=results/slurm_explore_%j.out

# ── Configuration ──
MAX_COMBOS="${MAX_COMBOS:-10}"
MAX_SIZE_GB="${MAX_SIZE_GB:-22.0}"
EASY="${EASY:-5}"
MEDIUM="${MEDIUM:-5}"
HARD="${HARD:-5}"
SEED="${SEED:-42}"
MAX_ITER="${MAX_ITER:-3}"
LANG="${LANG:-python3}"

# ── Setup ──
cd "$HOME/msc_onlab_1" || exit 1
source .venv/bin/activate
export OLLAMA_HOST="http://localhost:11434"
mkdir -p results

# ── Start Ollama inside the job so SLURM can reclaim its GPU on exit ──
echo "Starting Ollama server..."
ollama serve > /tmp/ollama_${SLURM_JOB_ID}.log 2>&1 &
OLLAMA_PID=$!
trap "kill $OLLAMA_PID 2>/dev/null" EXIT
for i in $(seq 1 30); do
    if curl -s http://localhost:11434/api/tags > /dev/null; then
        echo "Ollama ready (pid=$OLLAMA_PID)"
        break
    fi
    sleep 1
done

echo "Job $SLURM_JOB_ID started at $(date)"
echo "Node: $HOSTNAME"
echo "Max combos: $MAX_COMBOS | Max size: ${MAX_SIZE_GB}GB"
echo "=========================================="

python3 scripts/explore_models.py \
    --no-tunnel \
    --ollama-host "$OLLAMA_HOST" \
    --max-combos "$MAX_COMBOS" \
    --max-size-gb "$MAX_SIZE_GB" \
    --easy "$EASY" \
    --medium "$MEDIUM" \
    --hard "$HARD" \
    --seed "$SEED" \
    --max-iterations "$MAX_ITER" \
    --lang "$LANG"

echo "=========================================="
echo "Job finished at $(date)"
