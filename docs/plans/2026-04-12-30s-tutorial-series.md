# 30 秒 AI API 教学视频系列 — "Build with AI in 30 Seconds"

## 系列定位

**品牌**：`Build with AI in 30s` by SoxAI
**格式**：竖屏 1080x1920，30 秒，代码打字动画 + 语音讲解
**目标**：开发者看完就能照着做，每个视频解决一个具体问题
**发布频率**：每天 1-2 条（批量生成，定时发布）
**平台**：YouTube Shorts, TikTok, Instagram Reels

## 视频结构（固定模板）

```
[0-3s]  HOOK — 一句话抓注意力（大字 + 问题/结果展示）
[3-25s] CODE — 代码打字动画 + 语音讲解（展示完整可运行代码）
[25-30s] CTA — "soxai.io — Free $5 credit" + 品牌
```

## 系列规划（5 个主题线 × 6 集 = 30 个视频）

### Series 1: 🎮 AI + 游戏开发（6 集）

| # | 标题 | Hook | 代码内容 |
|---|------|------|---------|
| 1 | AI NPC Dialogue | "Give your NPCs a brain" | Python: 用 AI 生成 NPC 对话，根据玩家行为变化 |
| 2 | AI Dungeon Master | "AI writes your game story" | Python: AI 生成地牢探险的房间描述和事件 |
| 3 | AI Enemy Strategy | "Enemies that learn from you" | Python: AI 根据玩家行为生成敌人策略 |
| 4 | AI Item Generator | "Infinite unique weapons" | Python: AI 生成随机装备（名字+属性+描述） |
| 5 | AI Quest Generator | "Never run out of quests" | Python: AI 生成支线任务（目标+奖励+剧情） |
| 6 | AI Game Review | "AI playtests your game" | Python: AI 分析游戏日志给出改进建议 |

### Series 2: 🤖 AI + App 开发（6 集）

| # | 标题 | Hook | 代码内容 |
|---|------|------|---------|
| 1 | AI Chatbot | "Build a chatbot in 5 lines" | Python: 最简聊天机器人 |
| 2 | AI Translator | "Translate anything instantly" | Python: 实时多语言翻译 |
| 3 | AI Code Review | "AI reviews your PR" | Python: 读取 diff → AI 找 bug |
| 4 | AI Email Writer | "Never write emails again" | Python: 给定要点 → AI 写专业邮件 |
| 5 | AI Data Analyzer | "CSV to insights in seconds" | Python: 读 CSV → AI 总结趋势 |
| 6 | AI Image Describer | "AI sees your screenshots" | Python: 图片 → AI 描述内容 |

### Series 3: 🦞 AI + OpenClaw（6 集）

| # | 标题 | Hook | 代码内容 |
|---|------|------|---------|
| 1 | OpenClaw + AI Agent | "Build an AI agent that browses" | Python: OpenClaw agent 用 AI 决定下一步操作 |
| 2 | AI Web Scraper | "Scrape any site with AI" | Python: OpenClaw 抓网页 → AI 结构化提取数据 |
| 3 | AI Form Filler | "AI fills forms for you" | Python: AI 读取表单字段 → 自动填写 |
| 4 | AI Shopping Assistant | "AI finds the best deals" | Python: OpenClaw 浏览商品 → AI 对比价格 |
| 5 | AI Research Agent | "AI researches any topic" | Python: OpenClaw 搜索 → AI 总结多个来源 |
| 6 | AI Testing Agent | "AI tests your website" | Python: OpenClaw 浏览 → AI 找 UI bug |

### Series 4: 💼 AI + 企业场景（6 集）

| # | 标题 | Hook | 代码内容 |
|---|------|------|---------|
| 1 | AI Customer Support | "Auto-reply support tickets" | Python: 读取工单 → AI 生成回复 |
| 2 | AI Meeting Notes | "AI summarizes your meetings" | Python: 会议转录 → AI 提取要点和待办 |
| 3 | AI Report Generator | "Weekly reports in 10 seconds" | Python: 数据 → AI 生成 markdown 报告 |
| 4 | AI Contract Analyzer | "AI reads your contracts" | Python: 合同文本 → AI 标注风险条款 |
| 5 | AI Onboarding Guide | "AI trains your new hires" | Python: 公司文档 → AI 回答新人问题 |
| 6 | AI Competitor Monitor | "Track competitors with AI" | Python: 抓竞品页面 → AI 分析变化 |

### Series 5: ⚡ AI 技巧与对比（6 集）

| # | 标题 | Hook | 代码内容 |
|---|------|------|---------|
| 1 | GPT vs Claude | "Which is better for code?" | Python: 同一 prompt 发给两个模型，对比结果 |
| 2 | Save 90% on AI | "Use mini models wisely" | Python: 分类任务用 gpt-4o-mini 而不是 gpt-4o |
| 3 | AI Failover | "Never go down again" | Python: 主模型失败自动切换备用 |
| 4 | Stream AI Response | "Real-time AI output" | Python: SSE 流式输出 |
| 5 | AI with Memory | "AI that remembers context" | Python: 对话历史管理 |
| 6 | Batch AI Requests | "Process 1000 items fast" | Python: asyncio 并发调用 AI |

## 制作规格

- 分辨率：1080x1920（9:16 竖屏）
- 时长：28-32 秒
- 帧率：30fps
- 编码：H.264 + AAC
- 语音：Edge TTS（en_casual 或 zh_male）
- 字幕：内嵌大字（代码打字动画即是字幕）
- 品牌：每帧右下角 "sox.bot" 水印，结尾 "soxai.io"

## 双语策略

每个视频同时生成英文版和中文版：
- 英文版 → YouTube Shorts, TikTok (global)
- 中文版 → 抖音, 小红书, B站

## 自动化流程

```
1. 定义视频参数（topic, code, narration）
2. Edge TTS 生成语音
3. PIL 逐帧渲染代码打字动画
4. ffmpeg 合成最终视频
5. 可选：自动上传到 YouTube
```

全部 30 个视频可以一次性批量生成。
