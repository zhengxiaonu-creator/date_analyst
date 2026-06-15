"""统计分析标签页。"""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from data_analyzer.analysis import AdvancedAnalysis, DataProfiler
from data_analyzer.visualizer import DataVisualizer


def render(df: pd.DataFrame):
    st.header("📈 统计分析")

    profiler = DataProfiler(df)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = [c for c in df.select_dtypes(exclude=[np.number]).columns
                if df[c].nunique() <= 100]

    tab1, tab2, tab3 = st.tabs(["数值列统计", "分类列统计", "相关性矩阵"])

    with tab1:
        if not numeric_cols:
            st.info("当前数据集无数值列")
        else:
            stats = profiler.numeric_summary()
            st.dataframe(stats, use_container_width=True, height=360)
            st.subheader("🎯 单列详细分析")
            col = st.selectbox("选择数值列", numeric_cols, key="num_detail")
            stats_series = df[col].describe()
            st.json({
                "均值": round(float(stats_series.get("mean", 0)), 4),
                "中位数": round(float(stats_series.get("50%", 0)), 4),
                "标准差": round(float(stats_series.get("std", 0)), 4),
                "最小值": round(float(stats_series.get("min", 0)), 4),
                "最大值": round(float(stats_series.get("max", 0)), 4),
                "缺失数": int(df[col].isna().sum()),
                "缺失率(%)": round(float(df[col].isna().mean() * 100), 2),
            })

    with tab2:
        if not cat_cols:
            st.info("当前数据集无适合统计的分类列")
        else:
            col = st.selectbox("选择分类列", cat_cols, key="cat_detail")
            summary = profiler.categorical_summary(top_n=20)
            if col in summary:
                df_count = summary[col]
                left, right = st.columns([3, 2])
                with left:
                    st.dataframe(df_count, use_container_width=True, height=420)
                with right:
                    st.bar_chart(df_count["计数"], color="#E45756", height=420)

    with tab3:
        if len(numeric_cols) < 2:
            st.info("数值列少于 2 列，无法计算相关性")
        else:
            corr = profiler.correlation()
            st.dataframe(corr, use_container_width=True, height=360)
            viz = DataVisualizer(df)
            fig = viz.fig_heatmap()
            if fig is not None:
                st.pyplot(fig, use_container_width=True)

            st.subheader("🔗 与指定列的相关性排名")
            target = st.selectbox("目标列", numeric_cols, key="corr_target")
            adv = AdvancedAnalysis(df)
            top_corr = adv.top_correlations(target, top_n=min(5, len(numeric_cols) - 1))
            st.dataframe(top_corr, use_container_width=True)
