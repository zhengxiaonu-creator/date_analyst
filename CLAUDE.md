# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 用户约定

- **"打开Agent"** = 运行 `bash start.sh` 启动 Streamlit（自动清理旧进程，固定 8501 端口）
- **"上传github"** = 将当前项目最新状态提交并推送到 `https://github.com/zhengxiaonu-creator/date_analyst.git`（检查 git 状态，提交未提交变更，然后推送到 `origin main`）
- **"总结本次更新"** = 总结自上一次版本以来的所有改动内容，询问用户本次更新到哪个版本号，然后：更新 `agent.py` 的 AGENT_NAME、`__init__.py` 的 `__version__`、`app.py` 的侧边栏版本号和 `_CHANGELOG` 列表（头部追加新条目）、`CLAUDE.md` 的架构说明；**完成后自动上传至 GitHub**（提交并推送到 `origin main`）
- **Skill 调用约定**：当用户希望调用 Skill 时，优先选择本地已安装/项目内已有的 Skill；如果本地 Skill 不能满足需求，再优先调用 `find-skills` 搜索可安装 Skill，并在找到合适 Skill 后向用户说明再安装或使用。
- 完成任务后直接结束，请回复"mission completed!"

## 项目概述

数据分析Agent001 — 一个面向中文数据的轻量级交互式数据分析工具。支持 Streamlit Web 界面、命令行交互、Python API 三种使用方式。

## 常用命令

```bash
# 安装依赖
pip install -r requirements.txt

# 一键启动（自动清理旧进程 → 固定 8501 端口）
bash start.sh
# 等价于: pkill -f "streamlit run app.py" && python3 -m streamlit run app.py --server.headless true --server.port 8501

# 手动启动 Streamlit Web 界面
streamlit run app.py

# 命令行交互模式
python main.py examples/sample_data.csv

# 一次性命令
python main.py examples/sample_data.csv -c "完整报告"
python main.py examples/sample_data.csv -c "自动图表" -o ./outputs

# 生成示例数据
python examples/generate_sample.py

# 运行 Python API 示例
python examples/example_usage.py
```

## 架构

```
app.py                  # Streamlit 首页（引导 + 状态展示）
pages/                  # Streamlit 多页面目录（侧边栏自动导航）
  ├── 1_💬_对话Agent.py
  ├── 2_📊_数据概览.py
  ├── 3_🔎_数据查询.py
  ├── 4_📈_统计分析.py
  ├── 5_🖼️_可视化图表.py
  └── 6_🎯_分组聚合与异常.py
ui/                     # 页面渲染模块库（被 pages/ 中的薄壳脚本 import）
  ├── page_common.py    # 共享基础设施：setup_page()、get_df()、require_df()
  ├── sidebar.py        # 侧边栏：文件上传、LLM 配置、更新记录（写入 session_state）
  ├── tab_chat_agent.py # 对话式 Agent 渲染
  ├── tab_overview.py   # 数据概览渲染
  ├── tab_query.py      # 数据查询渲染
  ├── tab_analysis.py   # 统计分析渲染
  ├── tab_visualization.py # 可视化图表渲染
  └── tab_advanced.py   # 分组聚合 & 异常检测渲染
main.py                 # 命令行入口（argparse，交互模式 / -c 一次性命令）
data_analyzer/
  ├── __init__.py       # 包导出，版本号 0.00.04
  ├── constants.py      # 枚举定义：Intent（意图）、ChartType（图表类型）、CompareOp（比较操作）
  ├── router_rules.py   # RuleRouter：正则/关键词规则路由器（从 agent.py 拆分）
  ├── intent_executor.py # IntentExecutor：意图分发与执行器（从 agent.py 拆分）
  ├── conversation.py   # ConversationManager：对话历史管理器（从 agent.py 拆分）
  ├── data_loader.py    # DataLoader：CSV/Excel 加载，多编码自动回退（UTF-8→UTF-8-sig→GBK→latin-1）
  ├── analysis.py       # DataProfiler（概览/统计/相关性/完整报告） + AdvancedAnalysis（数据查询/排序/分组聚合/IQR异常值/透视表/Top相关）
  ├── visualizer.py     # DataVisualizer：每个图表有 fig_*（返回 Figure）和同名方法（保存 PNG）两套接口
  ├── agent.py          # DataAgent：协调路由模块，核心方法是 ask(question)
  └── llm_router.py     # LLMRouter：OpenAI 兼容 API 语义路由（意图分类 + 参数提取）
examples/
  ├── generate_sample.py  # 生成 500 行示例 CSV（含缺失值、异常值）
  └── example_usage.py    # DataAgent API 调用演示
tests/                  # 单元测试
  ├── test_agent.py
  ├── test_analysis.py
  ├── test_data_loader.py
  └── test_llm_router.py
outputs/                # 图表 PNG 输出目录（自动创建）
```

## 关键设计决策

- **双接口模式**：`DataVisualizer` 的每个图表方法都有两套 — `fig_*()` 返回 matplotlib Figure 给 Streamlit 用，同名无前缀方法保存 PNG 文件给 CLI 用。
- **Agent 路由**：`DataAgent.ask()` 按以下优先级处理请求：
  1. 正则匹配”加载/打开 xxx.csv” → 直接加载文件
  2. LLM 语义路由（`LLMRouter.route()` → 返回 `{intent, params, commentary}`）
  3. 回退规则路由（`RuleRouter.route()`：图表正则 → 分组聚合正则 → 异常值正则 → 查询正则 → 关键词匹配）
  4. `IntentExecutor` 根据意图类型分发执行

  支持的意图：概览、统计、分类列、相关性、数据查询、分组聚合、异常值检测、画图（直方图/箱线图/条形图/散点图/热力图）、自动图表、闲聊；不存在的工具会返回”当前功能不存在，请在 Agent 中加入新的数据分析功能”。
- **数据查询**：`🔎 数据查询` 页面直接复用 `AdvancedAnalysis.query_rows()`，支持关键词搜索、按列筛选、排序、当前结果/全部匹配结果 CSV 下载；对话 Agent 和 LLM 也通过 `query_data` 工具复用同一套查询能力。
- **数据加载**：`DataLoader` 同时支持本地文件路径和 Streamlit 上传文件对象（BytesIO），对 CSV 自动尝试多种中文编码。
- **Streamlit 多页面架构**：`pages/` 目录下每个 `.py` 文件是独立页面（Streamlit 自动识别生成侧边栏导航），`ui/` 是渲染模块库。每个子页面通过 `page_common.setup_page()` 统一初始化（页面配置 + CSS + 侧边栏），通过 `get_df()` / `require_df()` 从 session_state 获取数据。
- **中文字体**：`visualizer.py` 在 `sns.set_theme()` 之后配置中文字体回退链（顺序关键：seaborn 会重置 rcParams），macOS 优先使用 PingFang SC。
- **matplotlib 后端**：`visualizer.py` 强制 `matplotlib.use("Agg")`，确保无 GUI 环境（服务器/CLI）也能正常出图。
- **列名模糊匹配**：`DataAgent._validate_column()` 支持三级回退：精确匹配 → 忽略大小写匹配 → 子串模糊匹配。LLM 返回的列名同样经过此校验，因此用户说"销售额"时，实际列名"总销售额(元)"也能匹配。
- **查询双模式组合**：`AdvancedAnalysis.query_rows()` 的条件筛选和关键词搜索可以同时使用，两者叠加形成交集（而非互斥），结果再经过排序和 limit 截断。
- **Streamlit 缓存去重**：通过 `cached_source_key`（基于文件名+文件大小+Sheet 名）判断是否需要重新解析数据，避免同一文件被反复加载。
- **Excel 多 Sheet**：`DataLoader.list_sheets()` 可列出所有 sheet 名称，上传多 Sheet 的 Excel 文件时侧边栏自动弹出 Sheet 选择器。
