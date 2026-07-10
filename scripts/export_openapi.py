import json
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT_DIR / "contracts" / "openapi" / "mini-datadog.openapi.json"


def main() -> int:
    sys.path.insert(0, str(ROOT_DIR))

    from main import app

    CONTRACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONTRACT_PATH.write_text(
        json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Exported OpenAPI contract to {CONTRACT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
