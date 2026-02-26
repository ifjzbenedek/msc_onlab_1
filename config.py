import os
from dotenv import load_dotenv

# Load .env file from the project root
load_dotenv()

# Ollama
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11435")

# SSH tunnel
SSH_HOST = os.getenv("SSH_HOST", "152.66.244.201")
SSH_PORT = int(os.getenv("SSH_PORT", "46422"))
SSH_USER = os.getenv("SSH_USER", "ie350")
SSH_TUNNEL_LOCAL_PORT = int(os.getenv("SSH_TUNNEL_LOCAL_PORT", "11435"))
SSH_TUNNEL_REMOTE_PORT = int(os.getenv("SSH_TUNNEL_REMOTE_PORT", "11434"))

# LeetCode
LEETCODE_GRAPHQL_URL = os.getenv("LEETCODE_GRAPHQL_URL", "https://leetcode.com/graphql")
LEETCODE_SESSION = os.getenv("LEETCODE_SESSION", "")
