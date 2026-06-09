"""Streamlit Web 应用 - 数据分析Agent001 的可视化界面。

运行方式:
    streamlit run app.py
"""

from __future__ import annotations

import io
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

# 确保能从当前目录导入模块
sys.path.insert(0, str(Path(__file__).resolve().parent))

from data_analyzer import AGENT_NAME, DataLoader  # noqa: E402
from data_analyzer.analysis import AdvancedAnalysis, DataProfiler  # noqa: E402
from data_analyzer.visualizer import DataVisualizer  # noqa: E402


# ===================== 页面配置 =====================
st.set_page_config(
    page_title=f"{AGENT_NAME} - 可视化数据分析",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 自定义样式
st.markdown(
    """
    <style>
    .block-container { padding-top: 2rem; padding-bottom: 3rem; }
    .big-metric { font-size: 1.1rem; font-weight: 600; }
    .stTabs [data-baseweb="tab-list"] { gap: 12px; }
    .stTabs [data-baseweb="tab"] {
        height: 3rem; font-size: 1rem; border-radius: 8px 8px 0 0;
        padding: 0 18px; background-color: #f0f2f6;
    }
    .stTabs [aria-selected="true"] { background-color: #4C78A8 !important; color: white; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ===================== 侧边栏：数据上传 =====================
def render_sidebar() -> tuple[bool, str]:
    """渲染侧边栏：标题 + 文件上传 + 示例数据按钮。返回 (是否有数据, 文件名)"""
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
        )

        # 加载示例数据按钮
        use_sample = st.button("🎲 试试示例数据", use_container_width=True, type="secondary")

        st.divider()

        # === LLM API 配置 ===
        with st.expander("🤖 LLM 设置 (可选)", expanded=False):
            enable_llm = st.checkbox(
                "启用 LLM 语义理解",
                value=st.session_state.get("llm_enabled", False),
                help="使用大模型理解自然语言问题（需要 API Key）",
            )

            if enable_llm:
                # API Key：优先环境变量
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

                # 保存到 session_state
                st.session_state.llm_api_key = api_key
                st.session_state.llm_base_url = base_url
                st.session_state.llm_model = model
                st.session_state.llm_enabled = True
            else:
                st.session_state.llm_enabled = False

        st.divider()
        st.markdown("### 💡 使用提示")
        st.markdown(
            "- 上传后各标签页会自动填入对应列选项\n"
            "- 支持 GBK / UTF-8 等常见中文编码\n"
            "- Excel 多 sheet 可在上传后切换\n"
            "- 数据查询页支持关键词搜索、条件筛选、排序和下载\n"
            "- 对话式 Agent 也支持自然语言查询当前上传数据\n"
            "- 图表和报告可一键下载\n"
        )
        st.divider()

        # === 更新记录 ===
        _CHANGELOG = [
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

        with st.expander("📋 更新记录"):
            for entry in _CHANGELOG:
                st.markdown(f"**{entry['version']}** · {entry['date']}")
                for change in entry["changes"]:
                    st.markdown(f"  - {change}")
                if entry != _CHANGELOG[-1]:
                    st.divider()

        st.caption(f"V0.00.03 · 基于 Streamlit + Pandas")

    return uploaded, use_sample


# ===================== 页面1：数据概览 =====================
def tab_overview(df: pd.DataFrame, file_name: str):
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

    # CSV 下载
    st.subheader("📥 下载数据")
    csv_buffer = io.StringIO()
    df.head(1000).to_csv(csv_buffer, index=False, encoding="utf-8-sig")
    st.download_button(
        "⬇️ 下载前 1000 行 (CSV)",
        csv_buffer.getvalue(),
        file_name=f"preview_{Path(file_name).stem}.csv",
        mime="text/csv",
    )


# ===================== 页面2：数据查询 =====================
def tab_query(df: pd.DataFrame, file_name: str = ""):
    st.header(f"🔎 数据查询 · {file_name}")
    st.caption(f"支持关键词搜索、按列筛选、排序和下载。当前数据：{len(df):,} 行 × {len(df.columns):,} 列")

    adv = AdvancedAnalysis(df)
    all_cols = list(df.columns)
    numeric_cols = set(df.select_dtypes(include=[np.number]).columns)

    query_mode = st.radio(
        "查询方式",
        ["关键词搜索", "条件筛选"],
        horizontal=True,
        key="query_mode",
    )

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
                    "搜索关键词",
                    placeholder="例如：华东、张三、电子产品",
                    key="query_keyword",
                ).strip()
                match_label = st.radio(
                    "匹配方式",
                    ["包含匹配", "完整匹配"],
                    horizontal=True,
                    key="query_match_mode",
                )
                match_mode_value = "exact" if match_label == "完整匹配" else "contains"
                case_sensitive = st.checkbox("区分大小写", value=False, key="query_case_sensitive")
            with col_b:
                selected_columns = st.multiselect(
                    "搜索范围列（不选表示全表搜索）",
                    all_cols,
                    default=[],
                    key="query_search_cols",
                )
            if not keyword:
                can_query = False
                st.info("请输入关键词，或切换到条件筛选。")
        else:
            text_ops = {
                "等于": "eq",
                "不等于": "ne",
                "包含": "contains",
                "不包含": "not_contains",
                "为空": "isna",
                "非空": "notna",
            }
            numeric_ops = {
                "等于": "eq",
                "不等于": "ne",
                "大于": "gt",
                "大于等于": "gte",
                "小于": "lt",
                "小于等于": "lte",
                "为空": "isna",
                "非空": "notna",
            }

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
                        "筛选值",
                        placeholder="请输入要匹配或比较的值",
                        key="query_filter_value",
                    ).strip()

            if op not in ("isna", "notna") and filter_value == "":
                can_query = False
                st.info("请输入筛选值，或选择“为空/非空”。")
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
            conditions=conditions,
            keyword=keyword,
            columns=selected_columns or None,
            match_mode=match_mode_value,
            case_sensitive=case_sensitive,
            limit=display_limit,
            sort_by=sort_by,
            ascending=ascending,
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
            conditions=conditions,
            keyword=keyword,
            columns=selected_columns or None,
            match_mode=match_mode_value,
            case_sensitive=case_sensitive,
            limit=None,
            sort_by=sort_by,
            ascending=ascending,
        )
    except Exception:
        download_all = result

    st.caption("下载全部匹配结果可能需要几秒钟，取决于数据量。")
    down_a, down_b = st.columns(2)
    with down_a:
        current_buffer = io.StringIO()
        result.to_csv(current_buffer, index=False, encoding="utf-8-sig")
        st.download_button(
            "⬇️ 下载当前显示结果 CSV",
            current_buffer.getvalue(),
            file_name=f"query_current_{Path(file_name).stem}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with down_b:
        all_buffer = io.StringIO()
        download_all.to_csv(all_buffer, index=False, encoding="utf-8-sig")
        st.download_button(
            "⬇️ 下载全部匹配结果 CSV",
            all_buffer.getvalue(),
            file_name=f"query_all_{Path(file_name).stem}.csv",
            mime="text/csv",
            use_container_width=True,
        )


# ===================== 页面3：统计分析 =====================
def tab_analysis(df: pd.DataFrame):
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
            # 单列详细分析
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

            # 与指定列最相关
            st.subheader("🔗 与指定列的相关性排名")
            target = st.selectbox("目标列", numeric_cols, key="corr_target")
            adv = AdvancedAnalysis(df)
            top_corr = adv.top_correlations(target, top_n=min(5, len(numeric_cols) - 1))
            st.dataframe(top_corr, use_container_width=True)


# ===================== 页面3：可视化图表 =====================
def tab_visualization(df: pd.DataFrame):
    st.header("🖼️ 可视化图表")

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    all_cat_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()
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
            group = st.selectbox("分组列（可选）",
                                 ["不分组"] + cat_cols, key="box_group")
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
                # 每行 2 张
                for i in range(0, len(figures), 2):
                    cols = st.columns(2)
                    for j in range(2):
                        if i + j < len(figures):
                            title, fig = figures[i + j]
                            with cols[j]:
                                st.subheader(title)
                                st.pyplot(fig, use_container_width=True)


# ===================== 页面4：分组聚合 & 异常值 =====================
def tab_advanced(df: pd.DataFrame):
    st.header("🎯 分组聚合 & 异常检测")

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
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
                    # 绘制均值条形图（若存在）
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


# ===================== 页面5：对话式 Agent =====================
def tab_chat_agent(df: pd.DataFrame, file_name: str = ""):
    st.header("💬 对话式分析 Agent")

    # LLM 状态指示
    if st.session_state.get("llm_enabled"):
        model = st.session_state.get("llm_model", "unknown")
        st.caption(f"🤖 LLM 已启用 · 模型: {model} · 大模型优先理解需求并调用已有分析工具")
    else:
        st.caption("💡 提示：在侧边栏启用 LLM 可获得更好的自然语言理解能力")

    # 初始化 chat 历史
    if "messages" not in st.session_state:
        _reset_chat_messages()

    # 渲染历史消息（放在可滚动容器中，输入框始终在顶部可见）
    chat_container = st.container(height=500)
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "🧑"):
                st.markdown(msg["content"])

    # 输入框
    if prompt := st.chat_input("输入你的问题或命令..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="🧑"):
            st.markdown(prompt)

        # Agent 处理
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("思考中..."):
                agent = _get_or_create_agent(df, file_name)
                reply = agent.ask(prompt)

            # 尝试识别是否为图表生成路径 -> 直接渲染
            if reply.startswith("📉 已生成直方图 →") or reply.startswith("📦 已生成箱线图") or \
               reply.startswith("📊 已生成条形图 →") or reply.startswith("🗺️  已生成热力图") or \
               reply.startswith("🔵 已生成散点图"):
                st.markdown(reply)
                try:
                    path = reply.split("→", 1)[1].strip()
                    if Path(path).exists():
                        st.image(path, use_container_width=True)
                except Exception:
                    pass
            elif reply.startswith("📄 已生成"):
                st.markdown(reply)
            else:
                st.markdown(f"```\n{reply}\n```")

        st.session_state.messages.append({"role": "assistant", "content": reply})

    # 清空对话
    if st.sidebar.button("🗑️ 清空对话历史", use_container_width=True):
        _reset_chat_messages()
        agent = st.session_state.get("data_agent")
        if agent is not None and hasattr(agent, "set_conversation_history"):
            agent.set_conversation_history([])
        st.rerun()


def _reset_chat_messages():
    """重置对话开场白。"""
    st.session_state.messages = [{
        "role": "assistant",
        "content": (
            f"你好！我是 **{AGENT_NAME}** 🤖\n\n"
            "数据已经加载啦。试试这些问题：\n"
            "- `概览` 或 `完整报告`\n"
            "- `统计` 或 `分类列`\n"
            "- `相关性`\n"
            "- `查找 张三`\n"
            "- `查询 地区 是 华东`\n"
            "- `找出 销售额 大于 1000 的行`\n"
            "- `按 地区 聚合 销售额`\n"
            "- `检测 销售额 异常值`\n"
            "- `画 年龄 直方图`\n"
            "- `自动图表`"
        ),
    }]


def _invalidate_agent(reset_messages: bool = True):
    """数据源变化后清理会话级 Agent。"""
    st.session_state.data_version = st.session_state.get("data_version", 0) + 1
    st.session_state.pop("data_agent", None)
    st.session_state.pop("data_agent_key", None)
    if reset_messages:
        _reset_chat_messages()


def _get_or_create_agent(df: pd.DataFrame, file_name: str = ""):
    """内部工具：复用会话级 Agent，并在数据或 LLM 配置变化时重建。"""
    from data_analyzer.agent import DataAgent

    agent_key = (
        st.session_state.get("data_version", 0),
        st.session_state.get("llm_enabled", False),
        bool(st.session_state.get("llm_api_key")),
        st.session_state.get("llm_base_url", "https://api.openai.com/v1"),
        st.session_state.get("llm_model", "gpt-4o-mini"),
    )

    cached_agent = st.session_state.get("data_agent")
    if cached_agent is not None and st.session_state.get("data_agent_key") == agent_key:
        return cached_agent

    old_history = []
    if cached_agent is not None and hasattr(cached_agent, "get_conversation_history"):
        old_history = cached_agent.get_conversation_history()

    agent = DataAgent()
    agent.set_dataframe(df, file_name=file_name)
    if old_history:
        agent.set_conversation_history(old_history)

    # 配置 LLM（如果已启用且提供了 API Key）
    if st.session_state.get("llm_enabled") and st.session_state.get("llm_api_key"):
        agent.configure_llm(
            api_key=st.session_state["llm_api_key"],
            base_url=st.session_state.get("llm_base_url", "https://api.openai.com/v1"),
            model=st.session_state.get("llm_model", "gpt-4o-mini"),
        )

    st.session_state.data_agent = agent
    st.session_state.data_agent_key = agent_key
    return agent


# ===================== 主入口 =====================
def main():
    uploaded, use_sample = render_sidebar()

    # 主内容区
    st.title(f"📊 {AGENT_NAME}")
    st.caption("面向中文数据的轻量级交互式分析工具 — 上传文件 → 自动分析 → 生成图表")

    # 处理数据加载（优先级：上传 > 示例按钮）
    df: pd.DataFrame | None = st.session_state.get("cached_df", None)
    file_name = st.session_state.get("cached_name", "")

    # 新的上传
    if uploaded is not None:
        try:
            source_key = ("upload", uploaded.name, uploaded.size)
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
                    file_name = uploaded.name
                    if st.session_state.get("cached_source_key") != source_key:
                        uploaded.seek(0)
                        df = DataLoader().load(file_object=uploaded, file_name=uploaded.name)
            else:
                file_name = uploaded.name
                if st.session_state.get("cached_source_key") != source_key:
                    uploaded.seek(0)
                    df = DataLoader().load(file_object=uploaded, file_name=uploaded.name)

            if st.session_state.get("cached_source_key") != source_key:
                st.session_state.cached_df = df
                st.session_state.cached_name = file_name
                st.session_state.cached_source_key = source_key
                _invalidate_agent(reset_messages=True)
                st.toast(f"✅ 已加载 {file_name}", icon="🎉")
            else:
                df = st.session_state.cached_df
                file_name = st.session_state.cached_name
        except Exception as e:
            st.error(f"❌ 文件读取失败: {e}")
            df = None

    # 点击"示例数据"
    if use_sample:
        source_key = ("sample", "default")
        df = _generate_sample_data()
        file_name = "示例数据 (500 行 × 8 列)"
        st.session_state.cached_df = df
        st.session_state.cached_name = file_name
        st.session_state.cached_source_key = source_key
        _invalidate_agent(reset_messages=True)
        st.toast("✅ 已加载示例数据", icon="🎲")

    # 没有数据时的引导页面
    if df is None:
        st.info("👈 从左侧上传 CSV / Excel 文件，或点击 **试试示例数据** 开始探索。")
        st.divider()
        st.markdown(
            "### ✨ 我能做什么\n\n"
            "- 📊 **数据概览**：行数、列数、数据类型、缺失值统计、数据预览\n"
            "- 📈 **统计分析**：数值列描述统计 / 分类列频数 / 相关性矩阵\n"
            "- 🖼️ **可视化图表**：直方图、箱线图、条形图、散点图、热力图、缺失值图\n"
            "- 🔎 **数据查询**：主界面支持关键词搜索、按列筛选、排序和结果下载\n"
            "- 🎯 **分组聚合**：按任意列分组，对数值列做多种聚合\n"
            "- ⚠️ **异常值检测**：用 IQR 方法自动发现潜在异常\n"
            "- 💬 **对话式 Agent**：用自然语言提问，获得即时回答\n"
        )
        return

    # 有数据时渲染所有 tab（对话 Agent 在首位）
    tabs = st.tabs([
        "💬 对话式 Agent",
        "📊 数据概览",
        "🔎 数据查询",
        "📈 统计分析",
        "🖼️ 可视化图表",
        "🎯 分组聚合 & 异常",
    ])

    with tabs[0]:
        tab_chat_agent(df, file_name)
    with tabs[1]:
        tab_overview(df, file_name)
    with tabs[2]:
        tab_query(df, file_name)
    with tabs[3]:
        tab_analysis(df)
    with tabs[4]:
        tab_visualization(df)
    with tabs[5]:
        tab_advanced(df)


def _generate_sample_data() -> pd.DataFrame:
    """生成一份示例数据集，便于用户立刻体验功能。"""
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
    # 造缺失值和异常值
    df.loc[rng.choice(n, 25, replace=False), "评分"] = np.nan
    df.loc[rng.choice(n, 10, replace=False), "销售额"] = np.nan
    df.loc[rng.choice(n, 5, replace=False), "销售额"] *= 10
    return df


if __name__ == "__main__":
    main()
