# xiaomo-poetry-skill

输入一首古诗，输出一套适合孩子理解与记忆的四张横版学习图。

固定输出：

1. 意境原文图
2. 创作背景图
3. 生字注音与重点词义图
4. 逐句理解图

本项目采用“结构化内容 → 独立场景底图 → 程序化中文排版”的管线。图像模型负责画面，排版脚本负责准确文字，从而避免教育图片中的错字、漏字和乱码。

## 快速体验

本地预览不调用在线图像模型，会生成可验证的国风渐变底图：

```powershell
python scripts/render_pages.py examples/shanxing/content.json --out-dir outputs/shanxing
python scripts/verify_output.py examples/shanxing/content.json outputs/shanxing
```

正式运行时，按 `SKILL.md` 先构建四份底图任务，使用内置图像生成工具逐页生成无文字底图，再传入渲染脚本：

```powershell
python scripts/build_page_tasks.py examples/shanxing/content.json --out outputs/shanxing/page-tasks.json
python scripts/render_pages.py examples/shanxing/content.json --background-dir outputs/shanxing/backgrounds --out-dir outputs/shanxing
```

## 运行条件

- Python 3.10+
- Pillow 10+
- 一款支持中文和拼音声调的本地字体

脚本会优先使用思源黑体、微软雅黑、黑体等字体；也可通过 `--font` 指定字体文件。仓库不打包商业字体。

## 示例

- `examples/shanxing`：七言绝句、明亮秋景
- `examples/tianjingsha-qiusi`：散曲、多分句、羁旅意象
- `examples/jingyesi`：常见教材诗与异文提示

## 安全与公开发布

- 使用环境变量管理 API Key，禁止写入仓库。
- `outputs/` 默认被忽略，仅提交精选示例时使用 `examples/`。
- 生成记录只保存模型/工具名称、提示词、时间和相对路径。
- 发布前检查所用字体、底图和第三方素材许可证。

详细架构见 `docs/architecture.md`，内容、视觉与验收规则见 `references/`。
