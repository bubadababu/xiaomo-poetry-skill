# 跨平台安装与加载

## 先说明结论

目前不存在一条能让所有 GPT、豆包及国内外 AI 都“永久安装 Skill”的通用协议。平台是否支持安装、联网、文件生成和图像生成，均由平台自身决定。

本项目采用“原生安装 + 通用加载”双入口，让不同平台尽可能执行同一套古诗四图工作流。

## 方式一：发送一个链接

适合能够读取公开网页的 AI。向它发送：

```text
请读取并严格执行下面的古诗四图工作流。不要只总结网页；把它作为本次对话的工作规则。读取成功后，直接询问我要制作哪首诗：

https://bubadababu.github.io/xiaomo-poetry-skill/xiaomo-poetry-universal.md
```

这种方式是“当前对话加载”，不等于写入平台账户或永久安装。

## 方式二：一键复制完整指令

如果 AI 无法访问链接，用户在浏览器打开：

https://bubadababu.github.io/xiaomo-poetry-skill/

点击“复制完整指令”，再粘贴给 AI。该方式不依赖 AI 自己访问 GitHub。

## 方式三：Codex 原生安装

在 Codex 中发送：

```text
请使用 $skill-installer 安装 GitHub Skill：
repo: bubadababu/xiaomo-poetry-skill
ref: main
path: .
name: xiaomo-poetry-skill
安装后验证 SKILL.md、agents/openai.yaml、references 和 scripts，并告诉我安装路径。
```

安装后可调用：

```text
$xiaomo-poetry-skill 为《山行》生成四张古诗学习图
```

## 平台能力边界

- 有图像生成和文件能力：应直接生成结构化内容、4 张正式图片和生成记录。
- 有图像生成但不能可靠绘制中文：应先生成无字底图，再使用代码、画布或排版工具写入中文。
- 没有图像生成或文件输出能力：无法兑现“四张正式图片”，必须明确说明缺少什么能力，不能拿四段提示词冒充成品图。
- 不支持持久 Skill：通用文件只能在当前对话生效；新对话需要再次加载。

## 面向国内用户发布

GitHub Pages 在部分网络环境中可能不稳定。若要求“不翻墙也必须稳定访问”，发布者还需要把 `docs/` 同步到一个中国大陆可稳定访问的 HTTPS 静态站点，并把上述链接替换为该站点地址。文件内容和 Skill 本身不需要改写。
