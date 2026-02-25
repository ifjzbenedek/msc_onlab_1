import sys
sys.path.insert(0, ".")

import config
from src.clients import OllamaClient


def main() -> None:
    client = OllamaClient(host=config.OLLAMA_HOST)

    print(f"Connecting to Ollama at {config.OLLAMA_HOST} ...")

    print("\nFetching model list...")
    models = client.list_models()
    print(f"Found {len(models)} models:")
    for name in sorted(models):
        print(f"  - {name}")

    print("\nPing test (tinyllama)...")
    if client.ping():
        print("OK — model responded.")
    else:
        print("FAILED — model did not respond.")
        sys.exit(1)

    print("\nAll good!")


if __name__ == "__main__":
    main()
