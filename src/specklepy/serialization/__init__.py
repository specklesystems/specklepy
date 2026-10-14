from typing import Any

JSON_DEPRECATION: dict[str, Any] = {
    "reason": (
        "Since 2026.9 - JSON based send/receive pipelines are deprecated and replaced"
        " by the parquet bundle pipeline. See operations.send3 and operations.receive3"
        " for replacements, see https://docs.speckle.systems/next/welcome"
    ),
    "version": "2026.9.0",
}
