from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image

from common import PAGE_SPECS, load_json, output_filename
from validate_content import validate


def main() -> int:
    parser = argparse.ArgumentParser(description="验证四图交付物")
    parser.add_argument("content", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    content = load_json(args.content)
    errors, warnings = validate(content)
    expected = []
    for page, kind, _ in PAGE_SPECS:
        path = args.output_dir / output_filename(content, page, kind)
        expected.append(path)
        if not path.exists():
            errors.append(f"缺少图片：{path.name}")
            continue
        try:
            with Image.open(path) as image:
                if image.size != (1920, 1080):
                    errors.append(f"{path.name} 尺寸为 {image.size}，应为 1920×1080")
                if image.format != "PNG":
                    errors.append(f"{path.name} 不是 PNG")
        except Exception as exc:
            errors.append(f"无法读取 {path.name}：{exc}")
    for name in ("content.json", "generation.json"):
        if not (args.output_dir / name).exists():
            errors.append(f"缺少文件：{name}")
    generation_path = args.output_dir / "generation.json"
    if generation_path.exists():
        generation = load_json(generation_path)
        pages = generation.get("pages")
        if not isinstance(pages, list) or len(pages) != 4:
            errors.append("generation.json 必须记录 4 页")
        elif not all(page.get("visual_prompt") for page in pages if isinstance(page, dict)):
            errors.append("generation.json 每页必须保存 visual_prompt")
    for warning in warnings:
        print(f"WARNING: {warning}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"产物验证失败：{len(errors)} 个错误", file=sys.stderr)
        return 1
    print(f"产物验证通过：4 张 PNG，1920×1080，元信息完整；{len(warnings)} 个内容警告")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
