"""数据查询标签页。"""

from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from data_analyzer.analysis import AdvancedAnalysis


def render(df: pd.DataFrame, file_name: str = ""):
    st.header(f"🔎 数据查询 · {file_name}")
    st.caption(f"支持关键词搜索、按列筛选、排序和下载。当前数据：{len(df):,} 行 × {len(df.columns):,} 列")

    adv = AdvancedAnalysis(df)
    all_cols = list(df.columns)
    numeric_cols = set(df.select_dtypes(include=[np.number]).columns)

    query_mode = st.radio("查询方式", ["关键词搜索", "条件筛选"], horizontal=True, key="query_mode")

    with st.container(border=True):
        st.subheader("查询条件")
        keyword = None
        selected_columns: list[str] = []
        conditions: list[dict] = []
        match_mode_value = "contains"
        case_sensitive = False
        can_query = True

        if query_mode == "关键词搜索":
            col_a, col_b = st.columns([2, 3])
            with col_a:
                keyword = st.text_input(
                    "搜索关键词", placeholder="例如：华东、张三、电子产品",
                    key="query_keyword",
                ).strip()
                match_label = st.radio(
                    "匹配方式", ["包含匹配", "完整匹配"], horizontal=True,
                    key="query_match_mode",
                )
                match_mode_value = "exact" if match_label == "完整匹配" else "contains"
                case_sensitive = st.checkbox("区分大小写", value=False, key="query_case_sensitive")
            with col_b:
                selected_columns = st.multiselect(
                    "搜索范围列（不选表示全表搜索）",
                    all_cols, default=[], key="query_search_cols",
                )
            if not keyword:
                can_query = False
                st.info("请输入关键词，或切换到条件筛选。")
        else:
            text_ops = {"等于": "eq", "不等于": "ne", "包含": "contains",
                        "不包含": "not_contains", "为空": "isna", "非空": "notna"}
            numeric_ops = {"等于": "eq", "不等于": "ne", "大于": "gt",
                           "大于等于": "gte", "小于": "lt", "小于等于": "lte",
                           "为空": "isna", "非空": "notna"}

            col_a, col_b, col_c = st.columns([2, 2, 3])
            with col_a:
                filter_col = st.selectbox("筛选列", all_cols, key="query_filter_col")
            ops = numeric_ops if filter_col in numeric_cols else text_ops
            with col_b:
                op_label = st.selectbox("条件", list(ops.keys()), key="query_filter_op")
            op = ops[op_label]
            with col_c:
                if op in ("isna", "notna"):
                    filter_value = ""
                    st.text_input("筛选值", value="无需填写", disabled=True, key="query_filter_disabled")
                else:
                    filter_value = st.text_input(
                        "筛选值", placeholder="请输入要匹配或比较的值",
                        key="query_filter_value",
                    ).strip()

            if op not in ("isna", "notna") and filter_value == "":
                can_query = False
                st.info('请输入筛选值，或选择"为空/非空"。')
            else:
                conditions = [{"column": filter_col, "op": op, "value": filter_value}]

    st.subheader("排序与显示")
    sort_a, sort_b, sort_c = st.columns([2, 2, 2])
    with sort_a:
        sort_label = st.selectbox("排序列", ["不排序"] + all_cols, key="query_sort_col")
        sort_by = None if sort_label == "不排序" else sort_label
    with sort_b:
        sort_direction = st.radio("排序方向", ["升序", "降序"], horizontal=True, key="query_sort_direction")
        ascending = sort_direction == "升序"
    with sort_c:
        display_limit = st.selectbox("显示行数", [20, 50, 100, 500, 1000], index=1, key="query_display_limit")

    if not can_query:
        return

    try:
        result, total = adv.query_rows(
            conditions=conditions, keyword=keyword, columns=selected_columns or None,
            match_mode=match_mode_value, case_sensitive=case_sensitive,
            limit=display_limit, sort_by=sort_by, ascending=ascending,
        )
    except Exception as e:
        st.error(f"查询失败：{e}")
        return

    st.subheader("查询结果")
    metric_a, metric_b, metric_c = st.columns(3)
    metric_a.metric("匹配行数", f"{total:,}")
    metric_b.metric("当前显示", f"{len(result):,}")
    metric_c.metric("匹配率", f"{(total / len(df) * 100 if len(df) else 0):.2f}%")

    if total == 0:
        st.info("未找到匹配数据，请调整关键词、筛选条件或匹配方式。")
        return

    st.dataframe(result, use_container_width=True, height=420)

    try:
        download_all, _ = adv.query_rows(
            conditions=conditions, keyword=keyword, columns=selected_columns or None,
            match_mode=match_mode_value, case_sensitive=case_sensitive,
            limit=None, sort_by=sort_by, ascending=ascending,
        )
    except Exception:
        download_all = result

    st.caption("下载全部匹配结果可能需要几秒钟，取决于数据量。")
    down_a, down_b = st.columns(2)
    with down_a:
        current_buffer = io.StringIO()
        result.to_csv(current_buffer, index=False, encoding="utf-8-sig")
        st.download_button(
            "⬇️ 下载当前显示结果 CSV", current_buffer.getvalue(),
            file_name=f"query_current_{Path(file_name).stem}.csv",
            mime="text/csv", use_container_width=True,
        )
    with down_b:
        all_buffer = io.StringIO()
        download_all.to_csv(all_buffer, index=False, encoding="utf-8-sig")
        st.download_button(
            "⬇️ 下载全部匹配结果 CSV", all_buffer.getvalue(),
            file_name=f"query_all_{Path(file_name).stem}.csv",
            mime="text/csv", use_container_width=True,
        )
