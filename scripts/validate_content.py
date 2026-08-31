from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from common import is_slug, load_json, require_dict, require_text


def validate(content: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if content.get("schema_version") != "0.1.0":
        errors.append("schema_version 必须为 0.1.0")

    for key in ("slug", "title", "author", "dynasty", "genre"):
        require_text(content, key, "root", errors)
    if content.get("slug") and not is_slug(content["slug"]):
        errors.append("slug 只能包含 ASCII 小写字母、数字和连字符")

    full_text = content.get("full_text")
    if not isinstance(full_text, list) or not full_text or not all(
        isinstance(line, str) and line.strip() for line in full_text
    ):
        errors.append("full_text 必须是非空字符串数组")
        full_text = []

    source = require_dict(content, "source_note", errors)
    require_text(source, "version", "source_note", errors)
    if source.get("status") not in {
        "verified",
        "needs_review",
        "version_confirmation_required",
    }:
        errors.append("source_note.status 值无效")
    if not isinstance(source.get("warnings", []), list):
        errors.append("source_note.warnings 必须是数组")

    page1 = require_dict(content, "page1", errors)
    require_text(page1, "theme", "page1", errors)
    display = require_dict(page1, "display_text", errors)
    if display.get("title") != content.get("title"):
        errors.append("page1.display_text.title 必须与顶层 title 一致")
    require_text(display, "byline", "page1.display_text", errors)

    page2 = require_dict(content, "page2", errors)
    poet = require_dict(page2, "poet_intro", errors)
    for key in ("name", "identity", "style", "poem_relation"):
        require_text(poet, key, "page2.poet_intro", errors)
    background = require_dict(page2, "background", errors)
    for key in ("scene", "situation", "reason", "emotion"):
        require_text(background, key, "page2.background", errors)
    if background.get("certainty") not in {"high", "medium", "low"}:
        errors.append("page2.background.certainty 值无效")

    page3 = require_dict(content, "page3", errors)
    pinyin_items = page3.get("pinyin_items")
    if not isinstance(pinyin_items, list) or not pinyin_items:
        errors.append("page3.pinyin_items 必须是非空数组")
    else:
        for index, item in enumerate(pinyin_items):
            if not isinstance(item, dict):
                errors.append(f"page3.pinyin_items[{index}] 必须是对象")
                continue
            require_text(item, "word", f"page3.pinyin_items[{index}]", errors)
            require_text(item, "pinyin", f"page3.pinyin_items[{index}]", errors)
            word = item.get("word", "")
            if full_text and word not in "".join(full_text):
                warnings.append(f"注音词“{word}”未在 full_text 中原样出现")
    keyword_items = page3.get("keyword_items")
    if not isinstance(keyword_items, list) or not keyword_items:
        errors.append("page3.keyword_items 必须是非空数组")
    else:
        for index, item in enumerate(keyword_items):
            if not isinstance(item, dict):
                errors.append(f"page3.keyword_items[{index}] 必须是对象")
                continue
            require_text(item, "word", f"page3.keyword_items[{index}]", errors)
            require_text(item, "meaning", f"page3.keyword_items[{index}]", errors)

    page4 = require_dict(content, "page4", errors)
    explanations = page4.get("line_explanations")
    if not isinstance(explanations, list) or not explanations:
        errors.append("page4.line_explanations 必须是非空数组")
    else:
        explained = []
        for index, item in enumerate(explanations):
            if not isinstance(item, dict):
                errors.append(f"page4.line_explanations[{index}] 必须是对象")
                continue
            explained.append(require_text(item, "line", f"page4.line_explanations[{index}]", errors))
            require_text(item, "explanation", f"page4.line_explanations[{index}]", errors)
        normalized_source = [line.strip() for line in full_text]
        if explained and explained != normalized_source:
            errors.append("page4.line_explanations 必须按顺序逐行覆盖 full_text")
    require_text(page4, "summary", "page4", errors)

    style = require_dict(content, "visual_style", errors)
    require_text(style, "direction", "visual_style", errors)
    if style.get("aspect_ratio") != "16:9":
        errors.append("visual_style.aspect_ratio 必须为 16:9")
    palette = style.get("palette")
    if not isinstance(palette, list) or len(palette) < 3:
        errors.append("visual_style.palette 至少需要 3 个颜色")

    review = require_dict(content, "review_note", errors)
    if review.get("status") not in {"ready", "needs_review", "blocked"}:
        errors.append("review_note.status 值无效")
    if review.get("status") == "blocked":
        errors.append("review_note.status=blocked，不能生成正式图片")
    if source.get("status") != "verified":
        warnings.append("来源或版本尚未完全确认")
    warnings.extend(str(item) for item in source.get("warnings", []) if item)
    warnings.extend(str(item) for item in review.get("content_warnings", []) if item)

    return errors, list(dict.fromkeys(warnings))


def main() -> int:
    parser = argparse.ArgumentParser(description="校验古诗四图内容对象")
    parser.add_argument("content", type=Path)
    args = parser.parse_args()
    try:
        content = load_json(args.content)
    except Exception as exc:
        print(f"ERROR: 无法读取 JSON：{exc}", file=sys.stderr)
        return 2
    errors, warnings = validate(content)
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if errors:
        print(f"校验失败：{len(errors)} 个错误，{len(warnings)} 个警告", file=sys.stderr)
        return 1
    print(f"校验通过：0 个错误，{len(warnings)} 个警告")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
