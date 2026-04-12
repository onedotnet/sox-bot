# sox.bot — AI 驱动的社区运营自动化平台

> 设计文档 | 2026-04-12

## 概述

以 `sox.bot` 域名为中心，构建一套 AI bot 矩阵，每个 bot 扮演"营销团队"中的一个角色。所有 bot 背后调用 SoxAI 自身的 API（吃自己的狗粮），实现一个人维持一个 4 人营销团队的产出。

### 目标

- **核心用户**：企业 IT 团队（白标部署、团队配额管控、合规审计）
- **市场**：中国 + 海外双线并行
- **预算**：$200-500/月
- **成功指标**：入站企业线索量（询价/demo 请求），社区作为漏斗顶部支撑

### 核心叙事

"我们用自己的产品驱动营销" — sox.bot 本身就是 SoxAI 多模型能力的活广告，也是最好的客户案例。

---

## 整体架构

```
sox.bot（Web Dashboard — 运营控制台）
│
├── ScoutBot（线索猎手）
│   ├── 数据源：Reddit, Twitter/X, HN, 知乎, V2EX, GitHub Issues
│   ├── 监控关键词矩阵（中英双语）
│   ├── 输出：线索卡片（来源、原文、情感分析、建议回复草稿）
│   └── 人工审核门：所有回复必须审核后才发出
│
├── ContentBot（内容工厂）
│   ├── 输入：行业动态、竞品更新、产品 changelog、SEO 关键词
│   ├── 多模型协作：DeepSeek(大纲) → Claude(正文) → GPT-4o(翻译)
│   ├── 输出：博客草稿(中+英)、推文、知乎回答、LinkedIn 帖子
│   └── 内容日历：自动排期，审核后定时发布
│
├── CommunityBot（社区管家）
│   ├── 部署：Discord bot + 微信机器人
│   ├── 能力：RAG 技术问答、新人引导、FAQ
│   ├── 升级机制：无法回答 → @人工接管
│   └── 企业线索识别：检测信号 → 标记为 sales lead
│
└── AnalyticsBot（数据参谋）
    ├── 汇总：各渠道互动数据、线索漏斗、内容表现
    ├── 输出：每周运营周报（邮件+微信推送）
    └── 建议：基于数据推荐下周重点
```

### 技术选型

| 组件 | 技术 | 原因 |
|------|------|------|
| Bot 后端 | Python + FastAPI | AI/NLP 生态最丰富，快速迭代 |
| AI 引擎 | SoxAI API（自己的网关） | 吃自己的狗粮，多模型切换 |
| 调度 | Celery + Redis | 定时任务（内容排期、监控轮询） |
| 知识库 | SoxAI docs → Embedding → PGVector | CommunityBot 的 RAG 基础 |
| Dashboard | sox.bot 部署轻量 Next.js 控制台 | 审核、发布、数据看板 |
| 社交平台 API | Twitter API v2, Reddit API, Discord.py, 微信企业号 | 各平台发布和监控 |
| 存储 | PostgreSQL | 线索、内容、分析数据 |

### 月度成本估算

| 项目 | 费用 |
|------|------|
| SoxAI API 消耗（内容生成+社区回答+线索分析） | ~$80 |
| Twitter API Basic | $100 |
| Reddit API | 免费 |
| Discord bot | 免费 |
| 微信企业号 | 免费 |
| PGVector（自托管） | $0 |
| 服务器（可复用现有 VPS） | $0-50 |
| **合计** | **$180-230/月** |

---

## ScoutBot（线索猎手）

### 工作流程

```
每 30 分钟自动轮询
        │
        ▼
┌─────────────────────┐
│  多平台关键词搜索     │
│  Reddit / HN / X /   │
│  知乎 / V2EX / GitHub │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  AI 分析层（SoxAI）   │
│  1. 相关性评分 0-100  │
│  2. 意图分类          │
│  3. 情感分析          │
│  4. 生成回复草稿      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  过滤 & 去重          │
│  相关性 < 60 → 丢弃   │
│  已回复过 → 跳过       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  sox.bot Dashboard    │
│  线索卡片队列          │
│  审核/编辑/发布        │
└───────────────────── ┘
```

### 监控关键词矩阵

| 市场 | 平台 | 关键词 |
|------|------|--------|
| 海外 | Reddit (r/artificial, r/LocalLLaMA, r/devops) | "AI API gateway", "openrouter alternative", "LLM proxy", "manage AI API keys", "AI cost management", "multi-provider failover" |
| 海外 | HN, Twitter/X | "AI API pricing", "LLM for enterprise", "AI budget", "openai alternative" |
| 中国 | 知乎, V2EX | "大模型网关", "AI API 管理", "多模型调用", "企业AI成本", "OpenRouter替代", "API中转" |
| 通用 | GitHub Issues | 竞品仓库（litellm, one-api）的 issue/discussion 中的痛点讨论 |

### 意图分类 & 回复策略

| 意图 | 示例 | 回复策略 |
|------|------|---------|
| **求助型** | "有没有好用的多模型 API 管理方案？" | 直接推荐 SoxAI，附使用场景 |
| **吐槽型** | "OpenRouter 又挂了..." | 共情 + 提供备选方案 |
| **比较型** | "LiteLLM vs OpenRouter 哪个好？" | 客观对比 + 提出 SoxAI 差异点 |
| **技术型** | "怎么实现 AI API failover？" | 先给技术方案，自然带出 SoxAI |
| **企业型** | "我们团队 50 人需要..." | 高优先级，直接推荐 + 标记为 sales lead |

### 回复生成原则

AI system prompt 核心约束：

1. **绝不硬推销** — 先提供价值，最后自然提及 SoxAI
2. **符合平台文化** — Reddit 讨厌广告，HN 重技术深度，知乎偏长回答
3. **真人语气** — 开发者对开发者的口吻，不用营销话术
4. **诚实** — 如果竞品某方面更好，承认它，说清 SoxAI 的差异点
5. **带可验证信息** — 附代码示例、文档链接、价格对比表

### 线索卡片数据结构

```json
{
  "id": "scout_20260412_001",
  "source": "reddit",
  "subreddit": "r/devops",
  "url": "https://reddit.com/r/devops/...",
  "author": "enterprise_dev_42",
  "original_text": "We have 30 developers and need to...",
  "detected_at": "2026-04-12T10:30:00Z",
  "relevance_score": 87,
  "intent": "enterprise",
  "sentiment": "frustrated",
  "suggested_reply": "...(AI 生成的回复草稿)...",
  "priority": "high",
  "status": "pending_review"
}
```

### 反滥用设计

- **每个平台每天最多 3-5 条回复** — 避免被标记为 spam
- **账号活跃度维护** — 不只发推广，也正常参与讨论
- **人工审核门** — 所有回复必须审核后才发出，不做全自动发布
- **冷却期** — 同一个帖子/作者 30 天内只触达一次

---

## ContentBot（内容工厂）

### 多模型协作策略

| 阶段 | 模型 | 原因 | 成本/篇 |
|------|------|------|--------|
| 素材收集 & 大纲 | DeepSeek V3 | 便宜，擅长中文，结构化输出好 | ~$0.01 |
| 正文撰写 | Claude Sonnet | 写作质量最好，逻辑清晰 | ~$0.05 |
| 中英互译 | GPT-4o | 翻译质量稳定 | ~$0.03 |
| SEO 优化 | GPT-4o Mini | 简单任务，极便宜 | ~$0.001 |
| **单篇总成本** | | | **~$0.09** |

每月 20 篇双语内容 ≈ $2/月的 AI 成本。

### 内容类型矩阵

| 类型 | 频率 | 平台 | 目的 |
|------|------|------|------|
| **SEO 长文** | 2 篇/周 | Blog（中+英） | 搜索流量，长尾关键词 |
| **行业快评** | 3 条/周 | Twitter + 知乎 | 新模型发布/价格变动的快速点评 |
| **教程** | 1 篇/2 周 | Blog + GitHub | "如何用 SoxAI + X 框架做 Y" |
| **对比分析** | 1 篇/月 | Blog | "SoxAI vs OpenRouter vs LiteLLM" 保持更新 |
| **客户案例** | 有就写 | Blog + LinkedIn | 企业信任信号 |
| **Changelog 摘要** | 每次发版 | Blog + Twitter + Discord | 产品活跃度信号 |

### 内容日历自动排期

```
每周日晚自动生成下周内容计划：

周一: SEO 长文（英文）— 主题基于搜索趋势自动选取
周二: Twitter thread（英） + 知乎帖（中）— 行业快评
周三: SEO 长文（中文）— 周一英文版本的本地化+扩展
周四: Twitter 单条 + V2EX 帖 — 技术 tip / 对比数据
周五: LinkedIn 帖（英）— 偏企业视角的内容
周六: 缓冲日 — 补发 ScoutBot 发现的热点话题的回应
周日: 下周计划生成 + 周报
```

### 内容质量控制（三层检查）

| 检查层 | 方法 | 拦截条件 |
|--------|------|---------|
| **事实核查** | AI 自检 + 对照 SoxAI 文档 | 提及的功能/价格与文档不符 |
| **品牌一致性** | 规则检查 | 提及竞品时的用语是否中立、品牌名拼写 |
| **平台适配** | 字数/格式/标签检查 | Twitter ≤ 280 字、知乎 ≥ 500 字、正确 hashtag |

未通过任何一层 → 标记为"需人工修改"，不自动发布。

### SEO 关键词策略

**海外核心词**：ai api gateway, llm proxy, openrouter alternative, ai cost management, multi-provider ai api, ai api for enterprise, ai model routing

**中国核心词**：大模型网关, AI API 管理平台, 多模型调用, OpenRouter 替代, 企业 AI 成本控制, API 中转站

每篇 SEO 长文围绕 1 个主关键词 + 2-3 个长尾词构建。ContentBot 每月自动分析搜索趋势，更新关键词优先级。

---

## CommunityBot（社区管家）

### 双线社区布局

| 维度 | 海外 | 中国 |
|------|------|------|
| 主阵地 | Discord 服务器 | 微信群（企业微信） |
| 辅助 | GitHub Discussions | 飞书群（面向企业客户） |
| 入口 | sox.bot 网站 + docs + GitHub README | sox.bot 网站 + 知乎/V2EX 签名 |

### 意图路由

```
用户消息进入
      │
      ▼
  意图识别（SoxAI API）
      │
  ┌───┼──────┬──────────┬──────────┐
  ▼   ▼      ▼          ▼          ▼
技术问题 新人引导 闲聊/反馈  企业信号   超出能力
  │      │      │          │          │
  ▼      ▼      ▼          ▼          ▼
RAG 检索 发送   友好回应   私信通知    升级到
docs库  欢迎流程 记录反馈  标记lead    人工
回答问题 引导文档          CRM录入
```

### RAG 知识库

| 来源 | 内容 | 更新频率 |
|------|------|---------|
| `apps/website/src/content/docs/` | API 文档、指南、快速开始 | 每次部署自动同步 |
| `apps/website/src/content/blog/` | 博客文章 | 每次发布自动同步 |
| `CHANGELOG.md` | 版本更新记录 | 每次发版自动同步 |
| 历史问答 | 社区中人工回答过的问题 | 持续积累 |
| 竞品对比 FAQ | 手动维护的"SoxAI vs X"问答 | 每月更新 |

**技术方案**：文档 → chunking（按 heading 分段）→ Embedding（SoxAI 调 text-embedding-3-small）→ PGVector → 用户提问 → 相似度搜索 top-5 → Claude Sonnet 生成回答 + 文档链接

### 新人引导流程

**Discord**：用户加入 → 私信欢迎消息 + 角色选择（个人开发者/团队负责人/企业评估）→ 选择"企业评估"自动标记为 lead

**微信群**：新人入群 → 自动发送欢迎消息 + 快速开始链接 + 免费额度注册链接

### 企业线索识别信号

| 信号 | 示例 | 动作 |
|------|------|------|
| 团队规模 | "我们团队有 20 个开发者" | 标记 lead + 通知 |
| 预算相关 | "每月 AI API 预算大概 5000 美元" | 高优 lead |
| 合规需求 | "需要私有部署"、"数据不能出境" | 高优 lead + 推荐白标方案 |
| 竞品迁移 | "从 OpenRouter 迁移过来" | 标记 + 发送迁移指南 |
| 采购流程 | "能提供报价单吗"、"支持合同付款吗" | 最高优先级 → 立即通知 |

### 对话升级机制

| 场景 | CommunityBot 行为 |
|------|-------------------|
| 知识库能回答的技术问题 | 直接回答 + 附文档链接 |
| 知识库无法覆盖 | 升级到人工 |
| 用户不满/投诉 | 立即升级，不尝试自己处理 |
| 连续 2 次回答用户说"不对" | 自动升级 |
| 涉及账单/退款 | 直接升级 |
| 企业级需求 | 初步回应 + 升级 |

### Discord 频道结构

```
SoxAI Community
├── announcements      — 产品更新（管理员发布）
├── quickstart         — 新手引导（CommunityBot 活跃）
├── help               — 技术问答（CommunityBot + 人工）
├── show-and-tell      — 用户分享用 SoxAI 构建的项目
├── model-updates      — AI 模型发布/价格变动速报（ContentBot 自动发）
├── bug-reports        — Bug 反馈 → 自动创建 GitHub Issue
├── general            — 闲聊
└── enterprise         — 企业客户专属（需认证角色）
```

---

## AnalyticsBot（数据参谋）

### 数据采集源

| 来源 | 指标 |
|------|------|
| ScoutBot | 发现线索数、回复发布数、转化数 |
| ContentBot | 各平台发布数、阅读量、互动率 |
| CommunityBot | 社区成员数、问答数、自动解决率、企业线索数 |
| Google Analytics | 网站流量、来源渠道、注册转化 |
| SoxAI 平台 | 注册用户数、API 调用量、付费转化 |

### 每周运营周报

自动生成，发到邮箱和微信，包含：

- **本周概览**：关键指标 + 同比变化
- **ScoutBot 报告**：线索发现数、高价值企业线索列表
- **ContentBot 报告**：最佳/最差表现内容、AI 成本
- **CommunityBot 报告**：问答数、自动解决率、新企业线索
- **下周行动建议**：基于数据的 AI 生成建议（热门话题、高产出渠道、待跟进线索）

---

## sox.bot 控制台

你每天操作的唯一界面，设计目标：极度高效。

### 页面结构

| 路径 | 功能 |
|------|------|
| `/dashboard` | 总览仪表盘：今日待审核数、关键指标卡片、本周趋势图 |
| `/scout` | ScoutBot 管理：线索队列、一键操作（发布/编辑/忽略）、关键词配置 |
| `/content` | ContentBot 管理：内容日历、草稿预览、批准/编辑/重新生成 |
| `/community` | CommunityBot 管理：升级队列、企业线索列表、FAQ 知识库管理 |
| `/analytics` | 数据分析：多维度图表、线索漏斗、历史周报存档 |
| `/settings` | 配置：平台 API 密钥、通知偏好、AI 模型配置、排期规则 |

---

## 日常操作流程

### 每日（15 分钟）

```
08:00  打开 sox.bot/dashboard
       ├── 审核 ScoutBot 线索队列（3-5 条）→ 发布/忽略
       ├── 审核 ContentBot 今日待发内容（1-2 篇）→ 批准/微调
       └── 检查 CommunityBot 升级队列 → 回复需人工的问题
```

### 每周（30 分钟）

```
周日  阅读 AnalyticsBot 周报
      ├── 跟进未处理的企业线索
      ├── 审核下周内容计划
      └── 调整关键词/策略
```

### 每月（1 小时）

```
月初  回顾月度数据
      ├── 调整预算分配（哪个渠道 ROI 最高）
      ├── 更新竞品对比 FAQ
      └── 规划下月重点主题
```

---

## 分阶段路线图

| 阶段 | 时间 | 交付物 | 价值 |
|------|------|--------|------|
| **Phase 1** | 第 1-2 周 | ScoutBot + sox.bot 基础控制台 | 直接产出商业线索 |
| **Phase 2** | 第 3-4 周 | ContentBot + 内容日历 | 解决双线市场内容产出瓶颈 |
| **Phase 3** | 第 5-6 周 | CommunityBot（Discord + 微信） | 社区有人了才需要管家 |
| **Phase 4** | 持续 | AnalyticsBot + 生态集成 | 数据驱动优化 + 借力第三方社区 |

Phase 4 的生态集成包括：在 LangChain/CrewAI/Dify 社区中做技术贡献、发布 SoxAI Provider/Plugin。
