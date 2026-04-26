#!/bin/bash
# Logs per-GPU VRAM usage to a CSV file at fixed intervals (used as a background process inside SLURM jobs).

OUT="${1:-vram.csv}"
INTERVAL="${2:-2}"

nvidia-smi \
    --query-gpu=index,timestamp,memory.used,memory.total \
    --format=csv,noheader,nounits \
    --loop="$INTERVAL" \
    > "$OUT"
