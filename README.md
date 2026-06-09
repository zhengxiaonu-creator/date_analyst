# 📊 数据分析Agent001

一个面向中文数据的轻量级、交互式数据分析工具。当前版本：**V0.00.03**。

支持上传 CSV / Excel 数据后，在 Web 页面、命令行或 Python API 中完成数据概览、查询筛选、统计分析、可视化图表、分组聚合、异常值检测，以及对话式 Agent 问答。

## ✨ 核心能力

- 🌐 **Streamlit Web 界面**：6 个标签页覆盖常用数据分析流程，是最推荐的使用方式。
- 💬 **对话式 Agent**：用中文自然语言提问，自动路由到已有分析工具。
- 🧠 **可选 LLM 语义理解**：支持 OpenAI 兼容 API；启用后大模型先理解需求，再调用本地 Agent 工具执行分析。
- 🔎 **数据查询**：主界面和对话 Agent 均支持查找、筛选、排序当前上传数据。
- 🔧 **命令行工具**：适合脚本化、批处理和一次性分析命令。
- 🐍 **Python API**：可作为数据分析库集成到其他 Python 项目中。

## ⚡ 快速开始（推荐：Web 界面）

```bash
pip install -r requirements.txt
bash start.sh
```

`start.sh` 会自动清理旧的 Streamlit 进程，并固定使用 **8501** 端口启动应用。

也可以手动启动：

```bash
python3 -m streamlit run app.py --server.port 8501
```

打开浏览器访问 Streamlit 页面后，可以点击左侧 **「试试示例数据」** 立即体验，或上传自己的 CSV / Excel 文件。

## 🖥️ Web 界面功能

当前 Web 界面包含 6 个标签页：

| 标签页 | 功能 |
|---|---|
| 💬 对话式 Agent | 用自然语言提问，支持概览、统计、查询、聚合、异常值、图表等工具调用 |
| 📊 数据概览 | 展示行数、列数、缺失值、重复行、内存占用、列信息和数据预览 |
| 🔎 数据查询 | 支持关键词搜索、按列条件筛选、排序、匹配结果统计、CSV 下载 |
| 📈 统计分析 | 数值列统计、分类列频数、相关性矩阵、Top 相关性排名 |
| 🖼️ 可视化图表 | 直方图、箱线图、条形图、散点图、相关性热力图、缺失值图、一键图表 |
| 🎯 分组聚合 & 异常 | 任意列分组聚合、IQR 异常值检测、异常行展示 |

## 🤖 LLM 语义理解

在侧边栏 **LLM 设置** 中可选择启用大模型语义理解。该功能使用 OpenAI 兼容接口，支持手动填写：

- API Key
- Base URL
- 模型名称

界面内置快速预设：

- DeepSeek
- 通义千问
- 智谱 GLM
- 火山方舟

启用 LLM 后，对话式 Agent 的工作流程是：

1. 用户上传或加载数据文件。
2. Agent 将当前数据集结构、列名、类型、缺失值、示例值等信息提供给 LLMRouter 作为上下文。
3. 大模型只负责理解用户意图并返回标准 JSON 路由结果。
4. 本地 Agent 根据 intent 调用已有工具读取完整 DataFrame 并执行分析。
5. 如果用户需求没有对应工具，返回：`当前功能不存在，请在 Agent 中加入新的数据分析功能。`

> 说明：大模型不会直接编造分析结果；真正的数据读取、查询、统计和图表生成均由本地工具完成。

## 🔎 数据查询能力

V0.00.03 已将数据查询升级为主界面常用功能，同时也可通过对话 Agent / LLM 调用。

### 主界面查询

在 **🔎 数据查询** 标签页中支持：

- 关键词搜索：全表搜索或限定列搜索。
- 匹配方式：包含匹配 / 完整匹配。
- 大小写控制：可选择是否区分大小写。
- 条件筛选：等于、不等于、包含、不包含、大于、大于等于、小于、小于等于、为空、非空。
- 排序：按任意列升序或降序排列。
- 显示行数：20 / 50 / 100 / 500 / 1000。
- 结果下载：下载当前显示结果 CSV 或全部匹配结果 CSV。

### 对话式查询示例

```text
查找 华东
查询 地区 是 华东
找出 销售额 大于 1000 的行
搜索 商品名称 包含 手机
```

## 🚀 其他使用方式

### 命令行交互模式

```bash
python3 main.py examples/sample_data.csv
```

进入交互模式后可以输入：

```text
概览
统计
查找 华东
查询 地区 是 华东
找出 销售额 大于 1000 的行
按 地区 聚合 销售额
检测 销售额 异常值
画 年龄 直方图
自动图表
```

### 一次性命令模式

```bash
python3 main.py examples/sample_data.csv -c "完整报告"
python3 main.py examples/sample_data.csv -c "查找 华东"
python3 main.py examples/sample_data.csv -c "自动图表" -o ./outputs
```

### 生成示例数据

```bash
python3 examples/generate_sample.py
```

### Python API

```python
from data_analyzer import load_data, DataProfiler, DataVisualizer, DataAgent

# 加载数据
df = load_data("data.csv")

# 统计概览
profiler = DataProfiler(df)
print(profiler.full_report())

# 自动图表
viz = DataVisualizer(df, output_dir="outputs")
files = viz.auto_report()

# 对话式 Agent
agent = DataAgent()
agent.load_file("data.csv")
print(agent.ask("查找 华东"))
print(agent.ask("查询 地区 是 华东"))
print(agent.ask("找出 销售额 大于 1000 的行"))
print(agent.ask("按 地区 聚合 销售额"))
print(agent.ask("检测 销售额 异常值"))
```

也可以直接复用底层查询工具：

```python
from data_analyzer import load_data, AdvancedAnalysis

df = load_data("data.csv")
adv = AdvancedAnalysis(df)

result, total = adv.query_rows(
    conditions=[{"column": "销售额", "op": "gt", "value": 1000}],
    sort_by="销售额",
    ascending=False,
    limit=50,
)

print(f"共匹配 {total} 行")
print(result)
```

## 📁 项目结构

```text
数据分析Agent001/
├── app.py                         # Streamlit Web 界面（6 个标签页）
├── main.py                        # 命令行入口（交互模式 / 一次性命令）
├── start.sh                       # 启动脚本：清理旧进程并固定 8501 端口
├── requirements.txt               # 依赖列表
├── README.md                      # 项目说明文档
├── CLAUDE.md                      # 项目内 Claude Code 工作约定与架构说明
├── data_analyzer/                 # 核心分析模块
│   ├── __init__.py                # 包导出，版本号 0.00.03
│   ├── data_loader.py             # CSV / Excel 数据加载，多编码自动回退
│   ├── analysis.py                # 数据概览、统计、查询、排序、分组聚合、异常值、透视表、Top 相关
│   ├── visualizer.py              # 图表生成；支持保存 PNG 与返回 matplotlib Figure
│   ├── agent.py                   # DataAgent：自然语言入口、本地工具路由、LLM 优先路由
│   └── llm_router.py              # LLMRouter：OpenAI 兼容 API 意图分类与参数提取
├── examples/
│   ├── generate_sample.py         # 生成 500 行示例 CSV（含缺失值、异常值）
│   └── example_usage.py           # DataAgent API 调用演示
└── outputs/                       # 图表 PNG 输出目录（自动创建）
```

## ✨ 功能清单

| 模块 | 能力 |
|---|---|
| 📂 数据加载 | CSV / XLSX / XLS；UTF-8 / UTF-8-sig / GBK / latin-1 自动回退；Excel 多 Sheet |
| 📊 数据概览 | 行数、列数、缺失值、重复行、内存占用、列名、数据类型、缺失率 |
| 📈 数值列统计 | count / mean / std / min / 25% / 50% / 75% / 95% / max |
| 📋 分类列统计 | 每个分类值的计数与百分比（Top N） |
| 🔗 相关性矩阵 | Pearson 相关系数表、热力图、单列 Top 相关排名 |
| 🔎 数据查询 | 关键词搜索、按列筛选、数值比较、空值/非空、排序、CSV 下载 |
| 🎯 分组聚合 | 按任意列分组，对数值列执行 count / mean / median / min / max / std 等聚合 |
| ⚠️ 异常值检测 | IQR 方法，输出异常行和异常数量 |
| 📉 直方图 | 数值分布图，可调分箱数，可带 KDE 曲线 |
| 📦 箱线图 | 支持单数值列和按分类列分组对比 |
| 📊 条形图 | 分类列频数 Top N |
| 🔵 散点图 | 两个数值列的联合分布 |
| 🔥 热力图 | 数值列相关性矩阵可视化 |
| ❓ 缺失值图 | 各列缺失率可视化 |
| 🚀 一键图表 | 自动生成整套基础图表 |
| 💬 对话 Agent | 自然语言交互；启用 LLM 时优先语义路由，失败时回退关键词/正则路由 |
| 🧠 LLMRouter | 支持 OpenAI 兼容 API，将用户需求路由到 overview / summary / categorical / correlation / groupby_agg / outliers / chart / query_data / chat / unsupported |

## 🧠 Agent 支持的意图

| intent | 说明 |
|---|---|
| `overview` | 数据概览 / 完整报告 |
| `summary` | 数值列统计摘要 |
| `categorical` | 分类列统计 |
| `correlation` | 相关性分析 |
| `groupby_agg` | 分组聚合 |
| `outliers` | IQR 异常值检测 |
| `chart` | 图表生成：直方图、箱线图、条形图、散点图、热力图、自动图表 |
| `query_data` | 查询、查找、搜索、筛选当前已加载数据 |
| `chat` | 闲聊或使用说明 |
| `unsupported` | 当前 Agent 未实现的功能 |

当前未实现的需求，例如机器学习训练、预测建模、聚类、时间序列预测、外部数据库查询、多文件 join/merge、生成 Word/PPT 报告等，会被归类为 `unsupported`。

## 🧩 系统要求

- Python ≥ 3.9
- pandas
- numpy
- matplotlib
- seaborn
- openpyxl
- streamlit
- openai

安装依赖：

```bash
pip install -r requirements.txt
```

## 🧠 关于 CSV / Excel 读取

本项目使用内置 `DataLoader` 读取 CSV / Excel，不依赖外部 skill。当前已覆盖：

- 本地文件路径读取。
- Streamlit 上传文件对象读取。
- CSV 常见中文编码自动回退。
- Excel 多 Sheet 读取。

如果后续需要从 PDF / Word / 图片等非结构化文档中抽取表格，再评估引入专门的文档解析 skill。

## 📝 更新记录

### V0.00.03

- 🔎 主界面新增数据查询页：支持关键词搜索、按列筛选、排序和结果下载。
- 🧠 LLM 新增 `query_data` 工具路由：大模型可调用本地查询工具查找当前上传数据。
- 🧰 `AdvancedAnalysis` 新增 / 增强 `query_rows()`、`search_rows()`：支持等值、包含、数值比较、空值/非空查询、排序和完整结果返回。
- 💬 对话式 Agent 支持自然语言查询：如 `查找 华东`、`查询 地区 是 华东`、`找出 销售额 大于 1000`。
- 📥 查询结果支持下载当前显示结果和全部匹配结果 CSV。
- 📚 README、示例脚本和项目架构说明已同步更新。

### V0.00.02

- 🤖 新增 LLM 语义理解，支持 OpenAI 兼容 API。
- ⚙️ 侧边栏新增 LLM 设置面板，支持 DeepSeek / 通义千问 / 智谱 GLM / 火山方舟预设。
- 💬 对话式 Agent 标签页移至首位。
- 🔎 新增对话式数据查询能力。
- 🎯 分组聚合支持选择任意列作为分组列。
- 🔤 修复可视化图表中文字体显示问题。

### V0.00.01

- 🎉 初始版本发布。
- 📊 数据概览、统计分析、可视化图表、分组聚合、异常值检测。
- 💬 基于关键词路由的对话式 Agent。

## 🔜 后续扩展方向

- 支持数据库连接（MySQL / PostgreSQL / SQLite）。
- 支持大文件格式和处理方式（Parquet / Feather / 分块处理）。
- 支持分析结果导出 Markdown / PDF 报告。
- 支持更多高级分析工具，如机器学习建模、时间序列分析、多文件合并分析等。
