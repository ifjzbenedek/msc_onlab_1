## Setup

Need a `.env` file, venv, `pip install -r requirements.txt`.

```
# Accessing the remote server

OLLAMA_HOST=http://localhost:11435
SSH_HOST=152.66.244.201
SSH_PORT=46422
SSH_USER=<your username>
SSH_TUNNEL_LOCAL_PORT=11435
SSH_TUNNEL_REMOTE_PORT=11434

# Leetcode
LEETCODE_GRAPHQL_URL=https://leetcode.com/graphql
LEETCODE_SESSION=<your leetcode SESSIONID> (first you need to login)
```


## Scripts

Run from project root.

- `python scripts/test_connection.py` tunnel + ollama test
- `python scripts/test_leetcode_api.py` leetcode api test
- `python scripts/test_submit.py` submit a solution to leetcode
- `python scripts/test_model_coding.py --model qwen2.5-coder:32b --slug two-sum` solve one problem with a model
- `python scripts/fetch_problem_list.py` download problem list to `data/problem_list.json`
- `python scripts/benchmark.py --model qwen2.5-coder:32b` benchmark (10 easy + 10 medium + 10 hard, with leetcode submit)