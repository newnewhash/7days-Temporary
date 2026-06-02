# 7days-Temporary

自动化信息监控与 AI 摘要生成系统。

本项目通过定时任务抓取多个信息源（YouTube、Twitter/X 等），利用大语言模型生成中文 Markdown 摘要，集中归档到 `outputs/` 目录。

---

## 目录结构

```
7days-Temporary/
├── src/                          ← 源代码
│   ├── browser/                  ← 浏览器自动化（网页抓取、插件）
│   └── youtube_monitor/          ← YouTube 频道监控与摘要生成
├── outputs/                      ← 所有 AI 生成报告（GitHub Actions 自动提交）
│   ├── twitter/                  ← Twitter/X 每日财经摘要
│   ├── youtube/                  ← YouTube 视频中文 digest
│   └── daily/                    ← 每日宏观 + 加密市场简报
├── .github/workflows/            ← GitHub Actions 自动化配置
├── pyproject.toml                ← Python 依赖管理
└── README.md                     ← 本文件
```

### `src/` —— 源代码

所有可执行代码集中在这里，按信息源分子目录。

| 子目录 | 用途 |
|---|---|
| `src/browser/` | 浏览器自动化模块。`global_browser.py` 提供通用浏览器操作；`extension/` 存放浏览器插件。 |
| `src/youtube_monitor/` | YouTube 监控模块。每 12 小时检查指定频道，用 Gemini 生成中文摘要，输出到 `outputs/youtube/digests/`。详见该目录下的 [README](src/youtube_monitor/README.md)。 |

### `outputs/` —— 生成物（输出报告）

所有由 AI 自动生成的报告集中存放在此，**不应手动编辑**。

| 子目录 | 内容 | 更新方式 |
|---|---|---|
| `outputs/twitter/` | Twitter/X 每日财经摘要（`daily_finance_report_*.md` / `daily_twitter_summary_*.md`） | 外部工作流推送 |
| `outputs/youtube/digests/` | YouTube 视频中文摘要，按日期分子文件夹（`YYYY-MM-DD/*.md`） | GitHub Actions（每 12 小时） |
| `outputs/daily/` | 每日宏观 + 加密市场简报，按年月分子文件夹（`YYYY-MM/*.md`） | 外部工作流推送 |

### `.github/workflows/` —— 自动化

| 文件 | 说明 |
|---|---|
| `youtube-monitor.yml` | 每 12 小时运行 `src/youtube_monitor/monitor.py`，生成新视频摘要并自动提交到本仓库。 |

### 配置文件

| 文件 | 说明 |
|---|---|
| `pyproject.toml` | Python 项目依赖（使用 hatchling 构建）。 |
| `src/youtube_monitor/channels.json` | YouTube 监控目标频道列表。 |
| `src/youtube_monitor/state.json` | 运行时状态（已处理视频 ID、频道 ID 缓存），由 Actions 自动更新。**已加入 `.gitignore`，但 Actions 会强制提交。** |

---

## 快速开始

### YouTube 监控

1. 在仓库 Settings → Secrets → Actions 中添加：
   - `YOUTUBE_API_KEY`
   - `GEMINI_API_KEY`
2. 在 `src/youtube_monitor/channels.json` 中配置目标频道。
3. 手动触发 Actions：`.github/workflows/youtube-monitor.yml` → **Run workflow**。
   - 首次运行为基线建立，不会生成摘要。
   - 后续运行自动检测新视频并生成 digest。

---

## 注意事项

- `outputs/` 下的文件全部由 AI 自动生成，如需修改应在源模块中调整 prompt 或逻辑。
- `tmp/`、`state.json` 等运行时文件已加入 `.gitignore`，不会在本地提交。
- 如需扩展新的信息源（如 Podcast、Newsletter），建议在 `src/` 下新建子目录，输出统一放到 `outputs/` 对应分类中。
