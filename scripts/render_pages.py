from __future__ import annotations

import argparse
import hashlib
import math
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

from build_page_tasks import build_tasks
from common import PAGE_SPECS, load_json, output_filename, write_json
from validate_content import validate


WIDTH, HEIGHT = 1920, 1080
MARGIN = 72
PREVIEW_BG_NAMES = {page: f"{page:02d}-{kind}.png" for page, kind, _ in PAGE_SPECS}


def hex_color(value: str, fallback: tuple[int, int, int]) -> tuple[int, int, int]:
    value = value.lstrip("#")
    if len(value) == 6:
        try:
            return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))  # type: ignore[return-value]
        except ValueError:
            pass
    return fallback


def resolve_font(explicit: Path | None, serif: bool = False) -> Path:
    if explicit and explicit.exists():
        return explicit
    candidates = (
        [
            Path("C:/Windows/Fonts/simkai.ttf"),
            Path("C:/Windows/Fonts/STKAITI.TTF"),
            Path("/System/Library/Fonts/STHeiti Medium.ttc"),
        ]
        if serif
        else [
            Path("C:/Windows/Fonts/msyh.ttc"),
            Path("C:/Windows/Fonts/simhei.ttf"),
            Path("/System/Library/Fonts/PingFang.ttc"),
            Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
        ]
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("未找到支持中文的字体；请通过 --font 指定字体文件")


def font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size=size)


def wrap_text(draw: ImageDraw.ImageDraw, text: str, text_font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for paragraph in str(text).splitlines() or [""]:
        for char in paragraph:
            candidate = current + char
            if current and draw.textlength(candidate, font=text_font) > max_width:
                lines.append(current.rstrip())
                current = char.lstrip()
            else:
                current = candidate
        if current:
            lines.append(current.rstrip())
            current = ""
    return lines or [""]


def draw_wrapped(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    text_font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int, int] | tuple[int, int, int],
    max_width: int,
    line_gap: int = 10,
    max_lines: int | None = None,
) -> int:
    x, y = xy
    lines = wrap_text(draw, text, text_font, max_width)
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while last and draw.textlength(last + "…", font=text_font) > max_width:
            last = last[:-1]
        lines[-1] = last + "…"
    box = draw.textbbox((0, 0), "国Ag", font=text_font)
    line_height = box[3] - box[1]
    for line in lines:
        draw.text((x, y), line, font=text_font, fill=fill)
        y += line_height + line_gap
    return y


def panel(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], dark: bool = True) -> None:
    fill = (19, 24, 28, 214) if dark else (247, 242, 230, 224)
    stroke = (255, 248, 225, 55) if dark else (77, 55, 42, 45)
    draw.rounded_rectangle(box, radius=30, fill=fill, outline=stroke, width=2)


def fit_background(image: Image.Image) -> Image.Image:
    image = image.convert("RGB")
    scale = max(WIDTH / image.width, HEIGHT / image.height)
    resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
    left = (resized.width - WIDTH) // 2
    top = (resized.height - HEIGHT) // 2
    return resized.crop((left, top, left + WIDTH, top + HEIGHT))


def preview_background(content: dict[str, Any], page: int) -> Image.Image:
    palette = content["visual_style"].get("palette", [])
    top_color = hex_color(palette[0] if palette else "", (28, 36, 43))
    bottom_color = hex_color(palette[1] if len(palette) > 1 else "", (126, 72, 54))
    accent = hex_color(palette[2] if len(palette) > 2 else "", (226, 205, 169))
    image = Image.new("RGB", (WIDTH, HEIGHT), top_color)
    gradient_draw = ImageDraw.Draw(image)
    for y in range(HEIGHT):
        ratio = y / (HEIGHT - 1)
        color = tuple(int(top_color[channel] * (1 - ratio) + bottom_color[channel] * ratio) for channel in range(3))
        gradient_draw.line((0, y, WIDTH, y), fill=color)
    glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse((900, 80, 1740, 920), fill=(*accent, 50))
    glow = glow.filter(ImageFilter.GaussianBlur(150))
    image = Image.alpha_composite(image.convert("RGBA"), glow).convert("RGB")
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    seed = int(hashlib.sha256(f"{content['slug']}:{page}".encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    for layer in range(4):
        base_y = 600 + layer * 100
        points = [(-50, HEIGHT)]
        for x in range(-50, WIDTH + 100, 120):
            peak = base_y - rng.randint(45, 180) - int(70 * math.sin(x / 260 + layer))
            points.append((x, peak))
        points.extend([(WIDTH + 50, HEIGHT), (-50, HEIGHT)])
        alpha = 75 + layer * 28
        tone = tuple(max(0, channel - 25 - layer * 8) for channel in top_color)
        draw.polygon(points, fill=(*tone, alpha))
    if page == 1:
        draw.ellipse((1220, 100, 1450, 330), fill=(*accent, 175))
        draw.ellipse((1240, 120, 1430, 310), fill=(*accent, 55))
    for _ in range(70):
        x = rng.randrange(WIDTH)
        y = rng.randrange(HEIGHT)
        radius = rng.choice((1, 1, 2, 3))
        draw.ellipse((x, y, x + radius, y + radius), fill=(245, 229, 195, rng.randrange(12, 40)))
    overlay = overlay.filter(ImageFilter.GaussianBlur(1.2))
    image = Image.alpha_composite(image.convert("RGBA"), overlay)
    vignette = Image.new("L", (WIDTH, HEIGHT), 0)
    vdraw = ImageDraw.Draw(vignette)
    vdraw.ellipse((-250, -280, WIDTH + 250, HEIGHT + 330), fill=215)
    vignette = vignette.filter(ImageFilter.GaussianBlur(150))
    dark = Image.new("RGBA", (WIDTH, HEIGHT), (4, 8, 12, 125))
    image = Image.composite(image, Image.alpha_composite(image, dark), vignette)
    return image.convert("RGB")


def load_background(content: dict[str, Any], page: int, directory: Path | None) -> Image.Image:
    if directory is None:
        return preview_background(content, page)
    path = directory / PREVIEW_BG_NAMES[page]
    if not path.exists():
        raise FileNotFoundError(f"缺少第 {page} 页底图：{path}")
    return fit_background(Image.open(path))


def add_header(draw: ImageDraw.ImageDraw, content: dict[str, Any], page: int, sans: Path) -> None:
    draw.text((MARGIN, 48), content["title"], font=font(sans, 38), fill=(250, 244, 228, 245))
    label = PAGE_SPECS[page - 1][2]
    right = f"第 {page} 页  ·  {label}"
    fnt = font(sans, 25)
    length = draw.textlength(right, font=fnt)
    draw.text((WIDTH - MARGIN - length, 58), right, font=fnt, fill=(244, 232, 204, 205))
    draw.line((MARGIN, 108, WIDTH - MARGIN, 108), fill=(255, 246, 222, 70), width=2)


def render_cover(base: Image.Image, content: dict[str, Any], sans: Path, serif: Path) -> Image.Image:
    canvas = base.convert("RGBA")
    shade = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shade)
    sdraw.rectangle((910, 0, WIDTH, HEIGHT), fill=(5, 10, 15, 95))
    shade = shade.filter(ImageFilter.GaussianBlur(45))
    canvas = Image.alpha_composite(canvas, shade)
    draw = ImageDraw.Draw(canvas, "RGBA")
    panel(draw, (1020, 120, 1848, 1008))
    title_font = font(serif, 84 if len(content["title"]) <= 8 else 68)
    draw.text((1085, 190), content["title"], font=title_font, fill=(250, 238, 209, 255))
    draw.text((1089, 310), content["page1"]["display_text"]["byline"], font=font(sans, 31), fill=(224, 199, 158, 240))
    y = 405
    poem_font = font(serif, 42 if len(content["full_text"]) <= 4 else 37)
    for line in content["full_text"]:
        y = draw_wrapped(draw, (1085, y), line, poem_font, (252, 247, 233, 255), 690, line_gap=13)
        y += 16
    draw.text((MARGIN, HEIGHT - 102), content["page1"]["theme"], font=font(sans, 28), fill=(246, 231, 199, 220))
    return canvas.convert("RGB")


def render_background_page(base: Image.Image, content: dict[str, Any], sans: Path) -> Image.Image:
    canvas = ImageEnhance.Brightness(base).enhance(0.72).convert("RGBA")
    draw = ImageDraw.Draw(canvas, "RGBA")
    add_header(draw, content, 2, sans)
    left = (MARGIN, 150, 770, 1005)
    right = (810, 150, WIDTH - MARGIN, 1005)
    panel(draw, left)
    panel(draw, right)
    gold = (225, 184, 119, 255)
    white = (248, 244, 232, 255)
    muted = (219, 211, 194, 245)
    poet = content["page2"]["poet_intro"]
    draw.text((120, 205), "诗人介绍", font=font(sans, 45), fill=gold)
    draw.text((120, 285), poet["name"], font=font(sans, 58), fill=white)
    y = 380
    for label, value in (("身份", poet["identity"]), ("风格", poet["style"]), ("与本诗", poet["poem_relation"])):
        draw.text((120, y), label, font=font(sans, 28), fill=gold)
        y = draw_wrapped(draw, (120, y + 45), value, font(sans, 31), muted, 590, line_gap=11, max_lines=4) + 24
    bg = content["page2"]["background"]
    draw.text((865, 205), "创作背景", font=font(sans, 45), fill=gold)
    y = 292
    for label, value in (("场景", bg["scene"]), ("处境", bg["situation"]), ("为何写", bg["reason"]), ("情感", bg["emotion"])):
        draw.text((865, y), label, font=font(sans, 27), fill=gold)
        y = draw_wrapped(draw, (965, y - 2), value, font(sans, 30), white, 750, line_gap=10, max_lines=3) + 22
    certainty = {"high": "资料把握：较明确", "medium": "资料把握：大致可知", "low": "资料把握：需谨慎理解"}[bg["certainty"]]
    draw.text((865, 938), certainty, font=font(sans, 24), fill=(210, 194, 162, 220))
    return canvas.convert("RGB")


def render_words_page(base: Image.Image, content: dict[str, Any], sans: Path) -> Image.Image:
    canvas = ImageEnhance.Brightness(base).enhance(0.75).convert("RGBA")
    draw = ImageDraw.Draw(canvas, "RGBA")
    add_header(draw, content, 3, sans)
    left = (MARGIN, 150, 770, 1005)
    right = (810, 150, WIDTH - MARGIN, 1005)
    panel(draw, left)
    panel(draw, right)
    gold = (230, 190, 123, 255)
    white = (250, 246, 235, 255)
    muted = (218, 210, 193, 245)
    draw.text((120, 205), "生字注音", font=font(sans, 45), fill=gold)
    y = 300
    items = content["page3"]["pinyin_items"]
    item_gap = min(150, 600 // max(1, len(items)))
    for item in items:
        draw.text((120, y), item["word"], font=font(sans, 43), fill=white)
        draw.text((320, y + 7), item["pinyin"], font=font(sans, 32), fill=gold)
        note = item.get("note", "")
        if note:
            draw_wrapped(draw, (120, y + 62), note, font(sans, 27), muted, 575, line_gap=7, max_lines=2)
        y += item_gap
    draw.text((865, 205), "重点词义", font=font(sans, 45), fill=gold)
    y = 296
    keywords = content["page3"]["keyword_items"]
    item_gap = min(180, 650 // max(1, len(keywords)))
    for item in keywords:
        draw.text((865, y), item["word"], font=font(sans, 36), fill=gold)
        y2 = draw_wrapped(draw, (1090, y + 2), item["meaning"], font(sans, 30), white, 655, line_gap=9, max_lines=3)
        context_note = item.get("context_note", "")
        if context_note:
            draw_wrapped(draw, (1090, y2 + 3), context_note, font(sans, 25), muted, 655, line_gap=7, max_lines=2)
        y += item_gap
    return canvas.convert("RGB")


def render_meaning_page(base: Image.Image, content: dict[str, Any], sans: Path, serif: Path) -> Image.Image:
    canvas = ImageEnhance.Brightness(base).enhance(0.68).convert("RGBA")
    draw = ImageDraw.Draw(canvas, "RGBA")
    add_header(draw, content, 4, sans)
    items = content["page4"]["line_explanations"]
    columns = 2
    rows = math.ceil(len(items) / columns)
    summary_h = 135
    grid_top = 145
    grid_bottom = HEIGHT - MARGIN - summary_h - 20
    gap = 22
    card_w = (WIDTH - 2 * MARGIN - gap) // 2
    card_h = (grid_bottom - grid_top - gap * (rows - 1)) // rows
    gold = (230, 190, 123, 255)
    white = (250, 246, 235, 255)
    muted = (215, 207, 190, 240)
    for index, item in enumerate(items):
        row = index // columns
        col = index % columns
        x1 = MARGIN + col * (card_w + gap)
        y1 = grid_top + row * (card_h + gap)
        box = (x1, y1, x1 + card_w, y1 + card_h)
        panel(draw, box)
        draw.text((x1 + 32, y1 + 25), item["line"], font=font(serif, 34), fill=gold)
        y = draw_wrapped(draw, (x1 + 32, y1 + 83), item["explanation"], font(sans, 27), white, card_w - 64, line_gap=8, max_lines=3)
        image_or_emotion = item.get("image_or_emotion", "")
        if image_or_emotion and y < y1 + card_h - 38:
            draw_wrapped(draw, (x1 + 32, y + 5), "画面·" + image_or_emotion, font(sans, 23), muted, card_w - 64, line_gap=6, max_lines=2)
    summary_box = (MARGIN, HEIGHT - MARGIN - summary_h, WIDTH - MARGIN, HEIGHT - MARGIN)
    panel(draw, summary_box)
    draw.text((MARGIN + 34, summary_box[1] + 27), "全诗理解", font=font(sans, 30), fill=gold)
    draw_wrapped(draw, (MARGIN + 205, summary_box[1] + 29), content["page4"]["summary"], font(sans, 28), white, WIDTH - 2 * MARGIN - 245, line_gap=8, max_lines=2)
    return canvas.convert("RGB")


def render_all(content: dict[str, Any], out_dir: Path, background_dir: Path | None, font_path: Path | None) -> list[Path]:
    sans = resolve_font(font_path, serif=False)
    serif = resolve_font(font_path, serif=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    rendered: list[Path] = []
    for page, kind, _ in PAGE_SPECS:
        base = load_background(content, page, background_dir)
        if page == 1:
            final = render_cover(base, content, sans, serif)
        elif page == 2:
            final = render_background_page(base, content, sans)
        elif page == 3:
            final = render_words_page(base, content, sans)
        else:
            final = render_meaning_page(base, content, sans, serif)
        target = out_dir / output_filename(content, page, kind)
        final.save(target, format="PNG", optimize=True)
        rendered.append(target)
    return rendered


def main() -> int:
    parser = argparse.ArgumentParser(description="将结构化古诗内容排版为四张 PNG")
    parser.add_argument("content", type=Path)
    parser.add_argument("--background-dir", type=Path)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--font", type=Path)
    args = parser.parse_args()
    content = load_json(args.content)
    errors, warnings = validate(content)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    tasks = build_tasks(content)
    try:
        rendered = render_all(content, args.out_dir, args.background_dir, args.font)
    except Exception as exc:
        print(f"ERROR: 渲染失败：{exc}")
        return 2
    write_json(args.out_dir / "content.json", content)
    record = {
        "schema_version": "0.1.0",
        "skill_version": "0.1.0",
        "poem": {
            "slug": content["slug"],
            "title": content["title"],
            "author": content["author"],
            "dynasty": content["dynasty"],
            "version": content["source_note"]["version"],
        },
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "background_mode": "ai-background" if args.background_dir else "local-preview",
        "canvas": {"width": WIDTH, "height": HEIGHT, "format": "PNG"},
        "warnings": warnings,
        "pages": [
            {
                "page": task["page"],
                "theme": task["label"],
                "file": output_filename(content, task["page"], task["kind"]),
                "visual_prompt": task["prompt"],
            }
            for task in tasks
        ],
        "notes": "local-preview 仅用于离线排版测试；正式交付应使用四张独立 AI 底图。",
    }
    write_json(args.out_dir / "generation.json", record)
    print("已生成：")
    for path in rendered:
        print(path)
    print(args.out_dir / "content.json")
    print(args.out_dir / "generation.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
