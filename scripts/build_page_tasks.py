from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from common import PAGE_SPECS, load_json, write_json
from validate_content import validate


def compact_text_context(content: dict[str, Any], page: int) -> str:
    if page == 1:
        return f"诗题《{content['title']}》；{content['dynasty']}·{content['author']}；原文：{' '.join(content['full_text'])}"
    if page == 2:
        poet = content["page2"]["poet_intro"]
        bg = content["page2"]["background"]
        return f"诗人：{poet['identity']}；背景：{bg['scene']}；情感：{bg['emotion']}"
    if page == 3:
        words = "、".join(item["word"] for item in content["page3"]["pinyin_items"])
        keywords = "、".join(item["word"] for item in content["page3"]["keyword_items"])
        return f"生字：{words}；重点词：{keywords}"
    return f"逐句理解：{' '.join(content['full_text'])}；小结：{content['page4']['summary']}"


def prompt_for(content: dict[str, Any], page: int) -> str:
    palette = "、".join(content["visual_style"]["palette"])
    theme = content["page1"]["theme"]
    context = compact_text_context(content, page)
    shared = (
        f"Use case: {'historical-scene' if page < 3 else 'scientific-educational'}\n"
        f"Asset type: 16:9 古诗学习图第 {page} 页无文字底图\n"
        f"Primary request: 为《{content['title']}》生成“{PAGE_SPECS[page-1][2]}”页面的国风背景\n"
        f"Scene/backdrop: {theme}\n"
        f"Style/medium: {content['visual_style']['direction']}，电影感国风绘景，真实材质，克制高级，不低幼\n"
        f"Color palette: {palette}\n"
        f"Text context (semantic reference only): {context}\n"
    )
    composition = {
        1: "Composition/framing: 宽银幕沉浸式主视觉；为完整诗文预留一块大面积低细节安全区\n",
        2: "Composition/framing: 横版，保留两个清晰安静的信息安全区；景物主要位于边缘和远景\n",
        3: "Composition/framing: 横版，左右两个大面积低细节安全区；只用少量诗意景物点缀边缘\n",
        4: "Composition/framing: 横版，大部分区域明度稳定、低细节，适合逐句卡片和页尾小结\n",
    }[page]
    return shared + composition + (
        "Constraints: 不要绘制任何文字、汉字、拼音、书法、题签、印章、边框或水印；"
        "无现代物件；历史环境合理；同系列视觉语言\n"
        "Avoid: 错误文字、低幼卡通、办公PPT、密集拼贴、过度仙侠、抢占文字安全区的高频细节"
    )


def build_tasks(content: dict[str, Any]) -> list[dict[str, Any]]:
    tasks = []
    for page, kind, label in PAGE_SPECS:
        prompt = prompt_for(content, page)
        content[f"page{page}"]["visual_prompt"] = prompt
        tasks.append(
            {
                "page": page,
                "kind": kind,
                "label": label,
                "output_background": f"{page:02d}-{kind}.png",
                "prompt": prompt,
                "constraints": {
                    "independent_task": True,
                    "no_text_in_background": True,
                    "aspect_ratio": "16:9",
                },
            }
        )
    return tasks


def main() -> int:
    parser = argparse.ArgumentParser(description="构建四张独立底图任务")
    parser.add_argument("content", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--write-prompts-back", action="store_true")
    args = parser.parse_args()
    content = load_json(args.content)
    errors, warnings = validate(content)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    tasks = build_tasks(content)
    write_json(
        args.out,
        {
            "schema_version": "0.1.0",
            "poem": {"slug": content["slug"], "title": content["title"]},
            "warnings": warnings,
            "tasks": tasks,
        },
    )
    if args.write_prompts_back:
        write_json(args.content, content)
    print(f"已生成 4 个独立底图任务：{args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
