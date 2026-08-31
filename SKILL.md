---
name: xiaomo-poetry-skill
description: 为一首中国古诗、词或曲生成固定四页的“先理解、再记忆”横版学习图。适用于用户输入诗名、原文或结构化参数并要求古诗学习图、公众号配图或防死记硬背资料；最终必须交付结构化内容、4 张 PNG 和生成记录，而不是只给文案或提示词。
metadata:
  short-description: 一首古诗生成四张理解型学习图
---

# 古诗防死记硬背

把一首诗制作成四张 16:9 中文学习图：意境原文、创作背景、生字词义、逐句理解。产品承诺是“直接交付四图”，内部流程必须先冻结内容，再生成场景底图，最后精确排版。

## 执行流程

1. 解析诗名、作者、朝代、原文、年级、教材来源和风格。只有诗名时，补全通行或常见教材版本；存在异文或背景不确定时，写入 `review_note`，不要猜测。
2. 阅读 [内容规则](references/content-rules.md) 和 [数据结构](references/content-schema.md)，生成一个完整 `content.json`。四页只能引用这一个事实来源。
3. 运行：
   `python scripts/validate_content.py <content.json>`
   有错误则先修内容；警告必须保留到生成记录。
4. 阅读 [视觉规范](references/visual-system.md)，运行：
   `python scripts/build_page_tasks.py <content.json> --out <page-tasks.json>`
   得到四个相互独立的底图任务。
5. 默认使用内置图像生成工具逐页生成 4 张无文字场景底图。每页一次独立调用；不得把四页拼进一次调用。将最终底图依次保存为：
   `01-cover.png`、`02-background.png`、`03-words.png`、`04-meaning.png`。
6. 图像模型不负责最终中文。运行：
   `python scripts/render_pages.py <content.json> --background-dir <底图目录> --out-dir <输出目录>`
   由脚本准确写入标题、原文、拼音和讲解。
7. 运行：
   `python scripts/verify_output.py <content.json> <输出目录>`
   四图、尺寸、元信息或内容完整性任一失败，都不算完成。
8. 向用户返回 `content.json`、4 张正式 PNG、`generation.json` 的可点击路径；同时简短报告版本和核对提醒。

## 固定四页

1. `01-*-cover.png`：诗题、作者、朝代、完整原文；视觉最强。
2. `02-*-background.png`：明确分开的“诗人介绍”和“创作背景”。
3. `03-*-words.png`：明确分开的“生字注音”和“重点词义”。
4. `04-*-meaning.png`：逐句原文、白话解释、必要的意象或情感作用、全诗小结。

不得省页、换序或只输出 prompt。单页失败只重做该页。

## 质量边界

- 准确性高于画面效果；不确定信息使用审慎表述并显式标记。
- 优先采用用户指定教材版本，其次是常见教材或通行版本。
- 不把推测性的写作时间、地点、经历写成事实。
- 面向小学生及家长，自然讲解，不写百科拼接、空泛结论或机械直译。
- 正式图片采用程序化排版；不要依赖图像模型绘制大段中文。
- 四页统一系列感，但必须根据页面职责控制信息密度。
- 输出目录不得包含 API Key、隐私数据或绝对本地敏感路径。

如需调整模板、字号或安全区，先阅读 [视觉规范](references/visual-system.md)。发布或批量生成前，按 [验收清单](references/review-checklist.md) 检查。
