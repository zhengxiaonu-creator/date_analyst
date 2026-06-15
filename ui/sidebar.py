"""侧边栏渲染 — 文件上传、LLM 配置、更新记录。"""

from __future__ import annotations

import os

import pandas as pd
import streamlit as st

from data_analyzer import AGENT_NAME, DataLoader

_CHANGELOG = [
    {
        "version": "V0.00.04",
        "date": "2026-06-16",
        "changes": [
            "🏗️ Streamlit 多页面架构改造：从单页 st.tabs() 改为原生多页面侧边栏导航（pages/ 目录）",
            "🧠 Agent 核心模块化拆分：新增 constants.py（枚举）、router_rules.py（规则路由）、intent_executor.py（意图执行）、conversation.py（对话管理）",
            "🎨 新增 ui/ 渲染模块库：page_common.py（共享基础设施）、sidebar.py（侧边栏）、6 个 tab_*.py 渲染模块",
            "🐛 修复统计分析/可视化/分组聚合页面 render() 参数错误",
            "🐛 修复 app.py 和 sidebar.py 的 import 路径错误（pages → ui）",
            "✅ 新增 tests/ 单元测试目录（agent / analysis / data_loader / llm_router）",
            "☁️ 部署至 Streamlit Community Cloud",
        ],
    },
    {
        "version": "V0.00.03",
        "date": "2026-06-06",
        "changes": [
            "🔎 主界面新增数据查询页：支持关键词搜索、按列筛选、排序和结果下载",
            "🧠 LLM 新增 query_data 工具路由：大模型可调用本地查询工具查找当前上传数据",
            "🧰 AdvancedAnalysis 新增 query_rows/search_rows：支持等值、包含、数值比较、空值/非空查询",
            "💬 对话式 Agent 支持自然语言查询：如查找 华东、查询 地区 是 华东、找出 销售额 大于 1000",
            "📥 查询结果支持下载当前显示结果和全部匹配结果 CSV",
            "📚 更新 README 和示例脚本，补充数据查询用法与 DataLoader 说明",
        ],
    },
    {
        "version": "V0.00.02",
        "date": "2026-06-04",
        "changes": [
            "🤖 新增 LLM 语义理解：支持 OpenAI 兼容 API，关键词未匹配时自动调用大模型理解语义",
            "⚙️ 侧边栏新增 LLM 设置面板：支持 DeepSeek / 通义千问 / 智谱GLM / 火山方舟 一键预设",
            "💬 对话式 Agent 标签页移至首位，输入框固定顶部，对话历史可滚动",
            "🔎 新增数据查询：支持查找关键词、按列值筛选、数值条件查询当前上传数据",
            "🎯 分组聚合支持选择任意列作为分组列",
            "🔤 修复可视化图表中文字体显示问题",
        ],
    },
    {
        "version": "V0.00.01",
        "date": "2026-05-20",
        "changes": [
            "🎉 初始版本发布",
            "📊 数据概览：行数、列数、数据类型、缺失值统计、数据预览",
            "📈 统计分析：数值列描述统计 / 分类列频数 / 相关性矩阵",
            "🖼️ 可视化图表：直方图、箱线图、条形图、散点图、热力图",
            "🎯 分组聚合 & 异常值检测",
            "💬 对话式 Agent：关键词路由的自然语言交互",
        ],
    },
]


def render_sidebar() -> None:
    """渲染侧边栏：标题 + 文件上传 + 示例数据按钮 + LLM 配置 + 更新记录。

    数据通过 st.session_state.cached_df / cached_name 传递，不再通过返回值。
    """
    with st.sidebar:
        st.markdown(f"# 🤖 {AGENT_NAME}")
        st.caption("上传 CSV / Excel，立即开始分析")
        st.divider()

        # 文件上传
        uploaded = st.file_uploader(
            "📂 上传你的数据文件",
            type=["csv", "xlsx", "xls"],
            accept_multiple_files=False,
            help="支持 .csv / .xlsx / .xls 格式",
            key="sidebar_file_uploader",
        )

        # 加载示例数据按钮
        use_sample = st.button("🎲 试试示例数据", use_container_width=True, type="secondary")

        st.divider()

        # === LLM API 配置 ===
        _render_llm_settings()

        st.divider()
        st.markdown("### 💡 使用提示")
        st.markdown(
            "- 上传后各页面会自动填入对应列选项\n"
            "- 支持 GBK / UTF-8 等常见中文编码\n"
            "- Excel 多 sheet 可在上传后切换\n"
            "- 数据查询页支持关键词搜索、条件筛选、排序和下载\n"
            "- 对话式 Agent 也支持自然语言查询当前上传数据\n"
            "- 图表和报告可一键下载\n"
        )
        st.divider()

        _render_changelog()

        st.caption(f"V0.00.03 · 基于 Streamlit + Pandas")

    # 处理数据加载触发
    if uploaded is not None:
        _load_uploaded_file(uploaded)
    elif use_sample:
        _load_sample_data()


def _render_llm_settings():
    """渲染 LLM 配置面板。"""
    with st.expander("🤖 LLM 设置 (可选)", expanded=False):
        enable_llm = st.checkbox(
            "启用 LLM 语义理解",
            value=st.session_state.get("llm_enabled", False),
            help="使用大模型理解自然语言问题（需要 API Key）",
        )

        if enable_llm:
            default_key = os.environ.get("OPENAI_API_KEY", "")
            api_key = st.text_input(
                "API Key",
                type="password",
                value=st.session_state.get("llm_api_key", default_key),
                placeholder="sk-...",
                help="也支持 OPENAI_API_KEY 环境变量自动填充",
            )

            base_url = st.text_input(
                "Base URL",
                value=st.session_state.get(
                    "llm_base_url",
                    os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                ),
                placeholder="https://api.openai.com/v1",
                help="OpenAI 兼容接口地址",
            )

            model = st.text_input(
                "模型名称",
                value=st.session_state.get(
                    "llm_model",
                    os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
                ),
                placeholder="gpt-4o-mini / deepseek-chat / ep-xxxxxxxx",
                help="支持的模型：gpt-4o-mini, deepseek-chat, qwen-turbo, glm-4-flash, 火山方舟接入点ID 等",
            )

            # 快速预设
            st.caption("快速预设：")
            preset_cols = st.columns(4)
            if preset_cols[0].button("DeepSeek", use_container_width=True, key="preset_ds"):
                st.session_state.llm_base_url = "https://api.deepseek.com/v1"
                st.session_state.llm_model = "deepseek-chat"
                st.rerun()
            if preset_cols[1].button("通义千问", use_container_width=True, key="preset_qw"):
                st.session_state.llm_base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
                st.session_state.llm_model = "qwen-turbo"
                st.rerun()
            if preset_cols[2].button("智谱GLM", use_container_width=True, key="preset_glm"):
                st.session_state.llm_base_url = "https://open.bigmodel.cn/api/paas/v4"
                st.session_state.llm_model = "glm-4-flash"
                st.rerun()
            if preset_cols[3].button("火山方舟", use_container_width=True, key="preset_ark"):
                st.session_state.llm_base_url = "https://ark.cn-beijing.volces.com/api/v3"
                st.rerun()
            st.caption("⚠️ 火山方舟需填接入点ID（如 ep-2025xxxx），不是模型名")

            st.session_state.llm_api_key = api_key
            st.session_state.llm_base_url = base_url
            st.session_state.llm_model = model
            st.session_state.llm_enabled = True
        else:
            st.session_state.llm_enabled = False


def _render_changelog():
    """渲染更新记录。"""
    with st.expander("📋 更新记录"):
        for entry in _CHANGELOG:
            st.markdown(f"**{entry['version']}** · {entry['date']}")
            for change in entry["changes"]:
                st.markdown(f"  - {change}")
            if entry != _CHANGELOG[-1]:
                st.divider()


def _load_uploaded_file(uploaded) -> None:
    """处理上传文件加载，更新 session_state。"""
    try:
        source_key = ("upload", uploaded.name, uploaded.size)
        file_name = uploaded.name

        if uploaded.name.lower().endswith((".xlsx", ".xls")):
            sheets = DataLoader().list_sheets(file_object=uploaded)
            if len(sheets) > 1:
                sheet = st.sidebar.selectbox("📑 选择 Sheet", sheets, key="sheet_pick")
                source_key = ("upload", uploaded.name, uploaded.size, sheet)
                file_name = f"{uploaded.name} · Sheet: {sheet}"
                if st.session_state.get("cached_source_key") != source_key:
                    uploaded.seek(0)
                    df = DataLoader().load(file_object=uploaded, file_name=uploaded.name,
                                           sheet_name=sheet)
                else:
                    return
            else:
                if st.session_state.get("cached_source_key") != source_key:
                    uploaded.seek(0)
                    df = DataLoader().load(file_object=uploaded, file_name=uploaded.name)
                else:
                    return
        else:
            if st.session_state.get("cached_source_key") != source_key:
                uploaded.seek(0)
                df = DataLoader().load(file_object=uploaded, file_name=uploaded.name)
            else:
                return

        st.session_state.cached_df = df
        st.session_state.cached_name = file_name
        st.session_state.cached_source_key = source_key
        _invalidate_agent()
        st.toast(f"✅ 已加载 {file_name}", icon="🎉")
    except Exception as e:
        st.error(f"❌ 文件读取失败: {e}")


def _load_sample_data() -> None:
    """加载示例数据。"""
    source_key = ("sample", "default")
    if st.session_state.get("cached_source_key") == source_key:
        return

    import numpy as np
    rng = np.random.default_rng(42)
    categories = ["电子产品", "服装", "食品", "图书", "家居"]
    regions = ["华北", "华东", "华南", "华西", "东北"]
    genders = ["男", "女"]
    n = 500
    df = pd.DataFrame({
        "ID": range(1, n + 1),
        "类别": rng.choice(categories, n),
        "地区": rng.choice(regions, n),
        "性别": rng.choice(genders, n),
        "年龄": rng.integers(18, 65, n),
        "销售额": np.round(rng.exponential(500, n), 2),
        "数量": rng.integers(1, 10, n),
        "评分": np.round(rng.uniform(1.0, 5.0, n), 2),
    })
    df.loc[rng.choice(n, 25, replace=False), "评分"] = np.nan
    df.loc[rng.choice(n, 10, replace=False), "销售额"] = np.nan
    df.loc[rng.choice(n, 5, replace=False), "销售额"] *= 10

    file_name = "示例数据 (500 行 × 8 列)"
    st.session_state.cached_df = df
    st.session_state.cached_name = file_name
    st.session_state.cached_source_key = source_key
    _invalidate_agent()
    st.toast("✅ 已加载示例数据", icon="🎲")


def _invalidate_agent():
    """数据源变化后清理会话级 Agent。"""
    st.session_state.data_version = st.session_state.get("data_version", 0) + 1
    st.session_state.pop("data_agent", None)
    st.session_state.pop("data_agent_key", None)
    from ui.tab_chat_agent import reset_chat_messages
    reset_chat_messages()
