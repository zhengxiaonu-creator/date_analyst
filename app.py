"""Streamlit Web 应用 - 数据分析Agent001 首页。

运行方式:
    streamlit run app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# 确保能从当前目录导入模块
sys.path.insert(0, str(Path(__file__).resolve().parent))

from data_analyzer import AGENT_NAME  # noqa: E402
from ui.page_common import PAGE_CONFIG, SHARED_CSS  # noqa: E402
from ui.sidebar import render_sidebar  # noqa: E402

# ===================== 页面配置 =====================
st.set_page_config(**PAGE_CONFIG)
st.markdown(SHARED_CSS, unsafe_allow_html=True)

# 渲染侧边栏（上传文件、LLM 配置等）
render_sidebar()

# ===================== 首页内容 =====================
st.title(f"📊 {AGENT_NAME}")
st.caption("面向中文数据的轻量级交互式分析工具 — 上传文件 → 自动分析 → 生成图表")

df = st.session_state.get("cached_df")

if df is None:
    st.info("👈 从左侧上传 CSV / Excel 文件，或点击 **试试示例数据** 开始探索。")
    st.divider()
    st.markdown(
        "### ✨ 我能做什么\n\n"
        "- 📊 **数据概览**：行数、列数、数据类型、缺失值统计、数据预览\n"
        "- 📈 **统计分析**：数值列描述统计 / 分类列频数 / 相关性矩阵\n"
        "- 🖼️ **可视化图表**：直方图、箱线图、条形图、散点图、热力图、缺失值图\n"
        "- 🔎 **数据查询**：关键词搜索、按列筛选、排序和结果下载\n"
        "- 🎯 **分组聚合**：按任意列分组，对数值列做多种聚合\n"
        "- ⚠️ **异常值检测**：用 IQR 方法自动发现潜在异常\n"
        "- 💬 **对话式 Agent**：用自然语言提问，获得即时回答\n"
    )
else:
    file_name = st.session_state.get("cached_name", "")
    st.success(f"✅ 已加载数据：{file_name} · {len(df):,} 行 × {len(df.columns):,} 列")
    st.caption("👉 从左侧导航栏选择功能页面开始分析")
