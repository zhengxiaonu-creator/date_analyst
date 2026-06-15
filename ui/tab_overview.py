"""数据概览标签页。"""

from __future__ import annotations

import io
from pathlib import Path

import pandas as pd
import streamlit as st

from data_analyzer.analysis import DataProfiler


def render(df: pd.DataFrame, file_name: str):
    st.header(f"📊 数据概览 · {file_name}")

    profiler = DataProfiler(df)
    info = profiler.basic_info()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("行数", f"{info['行数']:,}")
    col2.metric("列数", f"{info['列数']:,}")
    col3.metric("缺失值", f"{info['缺失值总数']:,}")
    col4.metric("重复行", f"{info['重复行数']:,}")
    col5.metric("内存(MB)", f"{info['内存占用(MB)']}")

    st.subheader("🔍 数据预览")
    preview_rows = min(20, len(df))
    st.dataframe(df.head(preview_rows), use_container_width=True, height=300)

    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.subheader("📋 列信息")
        st.dataframe(profiler.data_types(), use_container_width=True, hide_index=True)
    with col_b:
        st.subheader("📐 数据类型占比")
        type_counts = (
            df.dtypes.astype(str)
            .replace({"int64": "整数", "float64": "浮点数", "object": "文本/分类",
                      "bool": "布尔", "datetime64[ns]": "日期"})
            .value_counts()
        )
        st.bar_chart(type_counts, color="#4C78A8", height=300)

    st.subheader("📥 下载数据")
    csv_buffer = io.StringIO()
    df.head(1000).to_csv(csv_buffer, index=False, encoding="utf-8-sig")
    st.download_button(
        "⬇️ 下载前 1000 行 (CSV)",
        csv_buffer.getvalue(),
        file_name=f"preview_{Path(file_name).stem}.csv",
        mime="text/csv",
    )
