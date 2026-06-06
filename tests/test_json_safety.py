from __future__ import annotations

import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from refugee_app.services.serializers import json_sanitize


def test_json_safety():
    obj = {"a": float("nan"), "b": float("inf"), "c": [1, float("nan")]}
    cleaned = json_sanitize(obj)
    json.dumps(cleaned, allow_nan=False)
    assert cleaned["a"] is None
    assert cleaned["b"] is None
    assert cleaned["c"][1] is None


if __name__ == "__main__":
    test_json_safety()
    print("JSON SAFETY OK")
