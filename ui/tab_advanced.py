"""分组聚合 & 异常值检测标签页。"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from data_analyzer.analysis import AdvancedAnalysis


def render(df: pd.DataFrame):
    st.header("🎯 分组聚合 & 异常检测")

    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    all_cols = df.columns.tolist()

    tab1, tab2 = st.tabs(["按列分组聚合", "异常值检测"])

    with tab1:
        st.markdown("#### 📊 分组聚合分析")
        c1, c2 = st.columns(2)
        g_col = c1.selectbox("分组列", all_cols, key="grp_col")
        v_col = c2.selectbox("数值列", numeric_cols, key="val_col") if numeric_cols else None

        if v_col and g_col:
            agg_funcs = st.multiselect(
                "选择聚合函数",
                ["count", "mean", "median", "min", "max", "std", "sum"],
                default=["count", "mean", "median", "max"],
            )
            if agg_funcs:
                adv = AdvancedAnalysis(df)
                result = adv.groupby_agg(g_col, v_col, agg_funcs)
                col_a, col_b = st.columns([3, 2])
                with col_a:
                    st.dataframe(result, use_container_width=True, height=440)
                with col_b:
                    if "mean" in result.columns:
                        st.bar_chart(result["mean"], color="#4C78A8", height=440)
                    elif "count" in result.columns:
                        st.bar_chart(result["count"], color="#E45756", height=440)

    with tab2:
        st.markdown("#### ⚠️ 异常值检测 (IQR 方法)")
        if not numeric_cols:
            st.info("无数值列可检测")
        else:
            target = st.selectbox("选择要检测的数值列", numeric_cols, key="outlier")
            adv = AdvancedAnalysis(df)
            odf = adv.outliers(target)
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.metric("异常行数", f"{len(odf):,}",
                          delta=f"{len(odf)/len(df)*100:.1f}% 占比")
                st.dataframe(odf.head(50), use_container_width=True, height=380)
            with col_b:
                st.info(
                    f"IQR 方法说明：\n\n"
                    f"- Q1 = 25% 分位数\n"
                    f"- Q3 = 75% 分位数\n"
                    f"- IQR = Q3 - Q1\n"
                    f"- 异常值 = < Q1-1.5·IQR 或 > Q3+1.5·IQR\n\n"
                    f"共检测 {len(df)} 行，发现 {len(odf)} 个异常点。"
                )
