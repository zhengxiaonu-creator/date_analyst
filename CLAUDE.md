# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 用户约定

- **"打开Agent"** = 运行 `bash start.sh` 启动 Streamlit（自动清理旧进程，固定 8501 端口）
- **"总结本次更新"** = 总结自上一次版本以来的所有改动内容，询问用户本次更新到哪个版本号，然后：更新 `agent.py` 的 AGENT_NAME、`__init__.py` 的 `__version__`、`app.py` 的侧边栏版本号和 `_CHANGELOG` 列表（头部追加新条目）、`CLAUDE.md` 的架构说明
- 完成任务后直接结束，请回复"mission completed!"

## 项目概述

数据分析Agent001 — 一个面向中文数据的轻量级交互式数据分析工具。支持 Streamlit Web 界面、命令行交互、Python API 三种使用方式。

## 常用命令

```bash
# 安装依赖
pip install -r requirements.txt

# 启动 Streamlit Web 界面（推荐）
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
app.py                  # Streamlit Web 界面（6 个标签页：对话Agent、概览、数据查询、统计、图表、分组/异常）
main.py                 # 命令行入口（argparse，交互模式 / -c 一次性命令）
data_analyzer/
  ├── __init__.py       # 包导出，版本号 0.00.03
  ├── data_loader.py    # DataLoader：CSV/Excel 加载，多编码自动回退（UTF-8→UTF-8-sig→GBK→latin-1）
  ├── analysis.py       # DataProfiler（概览/统计/相关性/完整报告） + AdvancedAnalysis（数据查询/排序/分组聚合/IQR异常值/透视表/Top相关）
  ├── visualizer.py     # DataVisualizer：每个图表有 fig_*（返回 Figure）和同名方法（保存 PNG）两套接口
  ├── agent.py          # DataAgent：关键词路由 + LLM 语义兜底，核心方法是 ask(question)
  └── llm_router.py     # LLMRouter：OpenAI 兼容 API 语义路由（意图分类 + 参数提取）
examples/
  ├── generate_sample.py  # 生成 500 行示例 CSV（含缺失值、异常值）
  └── example_usage.py    # DataAgent API 调用演示
outputs/                # 图表 PNG 输出目录（自动创建）
```

## 关键设计决策

- **双接口模式**：`DataVisualizer` 的每个图表方法都有两套 — `fig_*()` 返回 matplotlib Figure 给 Streamlit 用，同名无前缀方法保存 PNG 文件给 CLI 用。
- **Agent 路由**：`DataAgent.ask()` 在启用 LLM 时优先让大模型理解需求并路由到本地工具，未启用或 LLM 调用失败时回退关键词/正则路由。支持的意图：概览、统计、分类列、相关性、数据查询、分组聚合、异常值检测、画图（直方图/箱线图/条形图/散点图/热力图）、自动图表、闲聊；不存在的工具会返回“当前功能不存在，请在 Agent 中加入新的数据分析功能”。
- **数据查询**：主界面 `🔎 数据查询` 标签页直接复用 `AdvancedAnalysis.query_rows()`，支持关键词搜索、按列筛选、排序、当前结果/全部匹配结果 CSV 下载；对话 Agent 和 LLM 也通过 `query_data` 工具复用同一套查询能力。
- **数据加载**：`DataLoader` 同时支持本地文件路径和 Streamlit 上传文件对象（BytesIO），对 CSV 自动尝试多种中文编码。
- **Streamlit 状态管理**：`app.py` 用 `st.session_state.cached_df` 缓存已加载的 DataFrame，避免重复解析；Agent 对话历史也存储在 session_state 中。
- **中文字体**：`visualizer.py` 在 `sns.set_theme()` 之后配置中文字体回退链（顺序关键：seaborn 会重置 rcParams），macOS 优先使用 PingFang SC。
