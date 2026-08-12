"""List the Foundry Local models available on this machine.

    python -m localrag.models          # everything in the catalog
    python -m localrag.models --cached # only what is already downloaded

Aliases differ between platforms and change over time, so check here before
putting one in config.py or in LOCALRAG_CHAT_MODEL.
"""

from __future__ import annotations

import argparse
import sys

from . import config


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="List Foundry Local models.")
    parser.add_argument("--cached", action="store_true", help="only models already downloaded")
    args = parser.parse_args(argv)

    from foundry_local_sdk import Configuration, FoundryLocalManager

    FoundryLocalManager.initialize(Configuration(app_name=config.APP_NAME))
    manager = FoundryLocalManager.instance

    models = manager.catalog.get_cached_models() if args.cached else manager.catalog.list_models()
    if not models:
        print("No models found. Downloads happen on first use, e.g. python -m localrag.ingest")
        return 0

    print(f"{'alias':<34}{'capabilities':<28}{'context':>9}  cached")
    for model in sorted(models, key=lambda m: m.alias):
        capabilities = model.capabilities or "-"
        print(
            f"{model.alias:<34}{capabilities:<28}{model.context_length or 0:>9}"
            f"  {'yes' if model.is_cached else 'no'}"
        )

    print(f"\nIn use: chat={config.CHAT_MODEL}  embedding={config.EMBED_MODEL}")
    print(
        "Note: the model cache is per app name. These are the models visible to "
        f"'{config.APP_NAME}'."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
