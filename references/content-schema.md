# 内容对象规范

`content.json` 是四张图的唯一事实来源。文件使用 UTF-8，不含注释。

## 必填顶层字段

- `schema_version`：当前为 `0.1.0`
- `slug`：ASCII 小写文件标识，使用连字符
- `title`、`author`、`dynasty`、`genre`
- `full_text`：按展示行拆分的非空字符串数组
- `source_note`
- `page1`、`page2`、`page3`、`page4`
- `visual_style`
- `difficulty_level`
- `review_note`

## 来源与复核

```json
{
  "source_note": {
    "version": "常见现行教材版本",
    "source": "",
    "status": "verified",
    "warnings": []
  },
  "review_note": {
    "status": "ready",
    "content_warnings": [],
    "version_confirmation_required": false,
    "manual_review_items": []
  }
}
```

`source_note.status` 只使用：

- `verified`
- `needs_review`
- `version_confirmation_required`

`review_note.status` 只使用：

- `ready`
- `needs_review`
- `blocked`

`blocked` 表示不能安全生成正式图，例如诗名无法唯一确定、原文残缺且无法核对。

## 页面字段

```json
{
  "page1": {
    "theme": "页面主题",
    "display_text": {
      "title": "与顶层 title 一致",
      "byline": "朝代 · 作者"
    },
    "visual_prompt": "",
    "layout_variant": "cover-right-text"
  },
  "page2": {
    "poet_intro": {
      "name": "",
      "identity": "",
      "style": "",
      "poem_relation": ""
    },
    "background": {
      "scene": "",
      "situation": "",
      "reason": "",
      "emotion": "",
      "certainty": "high|medium|low"
    },
    "visual_prompt": "",
    "layout_variant": "two-column"
  },
  "page3": {
    "pinyin_items": [{"word": "", "pinyin": "", "note": ""}],
    "keyword_items": [{"word": "", "meaning": "", "context_note": ""}],
    "visual_prompt": "",
    "layout_variant": "words-split"
  },
  "page4": {
    "line_explanations": [
      {"line": "", "explanation": "", "image_or_emotion": ""}
    ],
    "summary": "",
    "visual_prompt": "",
    "layout_variant": "line-by-line"
  }
}
```

## 视觉字段

```json
{
  "visual_style": {
    "direction": "电影感国风学习图",
    "aspect_ratio": "16:9",
    "palette": ["#17202A", "#B35C44", "#E9DCC4"],
    "shared_elements": ["宣纸颗粒", "细线页码", "半透明信息面板"],
    "typography": {
      "title": "中文标题字体",
      "body": "高可读中文字体"
    },
    "series_id": "poem-slug"
  }
}
```

渲染脚本至少使用三种有效十六进制颜色；无法解析时回退到内置色板。
