"""可视化图表标签页。"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from data_analyzer.visualizer import DataVisualizer


def render(df: pd.DataFrame):
    st.header("🖼️ 可视化图表")

    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    all_cat_cols = df.select_dtypes(exclude=["number"]).columns.tolist()
    cat_cols = [c for c in all_cat_cols if 1 < df[c].nunique() <= 50]

    viz = DataVisualizer(df)

    chart_type = st.radio(
        "选择图表类型",
        ["📊 直方图 (数值分布)", "📦 箱线图 (含分组)", "📈 条形图 (分类频数)",
         "🔵 散点图 (双变量)", "🔥 相关性热力图", "❓ 缺失值分布"],
        horizontal=True,
    )

    st.divider()

    if "直方图" in chart_type:
        if not numeric_cols:
            st.info("无数值列可用")
        else:
            col = st.selectbox("选择数值列", numeric_cols, key="hist")
            bins = st.slider("分箱数量", 5, 100, 30)
            st.pyplot(viz.fig_histogram(col, bins), use_container_width=True)

    elif "箱线图" in chart_type:
        if not numeric_cols:
            st.info("无数值列可用")
        else:
            col = st.selectbox("选择数值列", numeric_cols, key="box")
            group = st.selectbox("分组列（可选）", ["不分组"] + cat_cols, key="box_group")
            st.pyplot(
                viz.fig_boxplot(col, None if group == "不分组" else group),
                use_container_width=True,
            )

    elif "条形图" in chart_type:
        if not cat_cols:
            st.info("无适合统计的分类列")
        else:
            col = st.selectbox("选择分类列", cat_cols, key="bar")
            top_n = st.slider("显示 Top N", 3, min(50, df[col].nunique()), 10)
            st.pyplot(viz.fig_barplot(col, top_n), use_container_width=True)

    elif "散点图" in chart_type:
        if len(numeric_cols) < 2:
            st.info("至少需要 2 个数值列")
        else:
            c1, c2 = st.columns(2)
            x = c1.selectbox("X 轴", numeric_cols, key="scatter_x")
            y_options = [c for c in numeric_cols if c != x]
            y = c2.selectbox("Y 轴", y_options, key="scatter_y")
            st.pyplot(viz.fig_scatter(x, y), use_container_width=True)

    elif "热力图" in chart_type:
        fig = viz.fig_heatmap()
        if fig is None:
            st.info("数值列不足")
        else:
            st.pyplot(fig, use_container_width=True)

    elif "缺失值" in chart_type:
        st.pyplot(viz.fig_missing_map(), use_container_width=True)

    # 一键生成全套图表
    st.divider()
    if st.button("🚀 一键生成全套分析图表", type="primary", use_container_width=True):
        with st.spinner("正在生成所有图表..."):
            figures = viz.auto_report_figures()
            if not figures:
                st.warning("未能生成任何图表")
            else:
                st.success(f"已生成 {len(figures)} 张图表")
                for i in range(0, len(figures), 2):
                    cols = st.columns(2)
                    for j in range(2):
                        if i + j < len(figures):
                            title, fig = figures[i + j]
                            with cols[j]:
                                st.subheader(title)
                                st.pyplot(fig, use_container_width=True)
