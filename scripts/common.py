from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


PAGE_SPECS = (
    (1, "cover", "意境原文"),
    (2, "background", "创作背景"),
    (3, "words", "生字注音与重点词义"),
    (4, "meaning", "逐句理解"),
)


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: str | Path, data: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def output_filename(content: dict[str, Any], page: int, kind: str) -> str:
    return f"{page:02d}-{content['slug']}-{kind}.png"


def is_slug(value: str) -> bool:
    return bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value))


def require_dict(parent: dict[str, Any], key: str, errors: list[str]) -> dict[str, Any]:
    value = parent.get(key)
    if not isinstance(value, dict):
        errors.append(f"{key} 必须是对象")
        return {}
    return value


def require_text(parent: dict[str, Any], key: str, path: str, errors: list[str]) -> str:
    value = parent.get(key)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{path}.{key} 必须是非空字符串")
        return ""
    return value.strip()
