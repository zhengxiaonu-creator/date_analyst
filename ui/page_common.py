"""多页面共享工具：页面配置、侧边栏渲染、数据获取。"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# 确保 ui/ 和 data_analyzer/ 可被 import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data_analyzer import AGENT_NAME  # noqa: E402

# 所有页面统一的配置
PAGE_CONFIG = {
    "page_title": f"{AGENT_NAME} - 可视化数据分析",
    "page_icon": "📊",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}

SHARED_CSS = """
<style>
.block-container { padding-top: 2rem; padding-bottom: 3rem; }
.big-metric { font-size: 1.1rem; font-weight: 600; }
</style>
"""


def setup_page():
    """每个子页面开头调用：设置 page_config + 注入共享 CSS + 渲染侧边栏。"""
    st.set_page_config(**PAGE_CONFIG)
    st.markdown(SHARED_CSS, unsafe_allow_html=True)
    from ui.sidebar import render_sidebar
    render_sidebar()


def get_df() -> tuple:
    """从 session_state 获取当前数据。返回 (df, file_name)。

    df 可能为 None（用户尚未上传数据）。
    """
    df = st.session_state.get("cached_df")
    file_name = st.session_state.get("cached_name", "")
    return df, file_name


def require_df():
    """从 session_state 获取数据，若无数据则显示引导提示并 stop()。"""
    df, file_name = get_df()
    if df is None:
        st.info("👈 从左侧上传 CSV / Excel 文件，或点击 **试试示例数据** 开始探索。")
        st.stop()
    return df, file_name
