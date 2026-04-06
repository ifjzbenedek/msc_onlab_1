#!/bin/bash
# One-time setup on the GPU server.
# Run this after uploading the project:
#   ssh -p 46422 bzoltan@152.66.244.201 "bash ~/msc_onlab_1/slurm/setup_server.sh"

set -e

PROJECT_DIR="$HOME/msc_onlab_1"
cd "$PROJECT_DIR"

echo "=== Creating virtual environment ==="
python3 -m venv .venv
source .venv/bin/activate

echo "=== Installing dependencies ==="
pip install --upgrade pip
pip install -r requirements.txt

echo "=== Creating .env for server ==="
if [ ! -f .env ]; then
    cat > .env << 'EOF'
# Server-side config (Ollama is local, no SSH tunnel needed)
OLLAMA_HOST=http://localhost:11434

# LeetCode
LEETCODE_GRAPHQL_URL=https://leetcode.com/graphql
LEETCODE_SESSION=PASTE_YOUR_SESSION_HERE
EOF
    echo ".env created — edit it to add your LEETCODE_SESSION!"
else
    echo ".env already exists, skipping"
fi

echo "=== Fetching problem list ==="
mkdir -p data
if [ ! -f data/problem_list.json ]; then
    python3 scripts/fetch_problem_list.py
else
    echo "problem_list.json already exists, skipping"
fi

echo "=== Setup done ==="
