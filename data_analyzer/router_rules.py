"""关键词/正则路由模块 — 从 DataAgent._ask_by_rules 拆分出来的路由逻辑。"""

from __future__ import annotations

import logging
import re
from typing import Optional

from .constants import (
    QUERY_TRIGGERS,
    QUERY_VALUE_STRIP_CHARS,
    COMPARE_TOKENS,
    ChartType,
    CompareOp,
)

logger = logging.getLogger(__name__)


class RuleRouter:
    """基于关键词和正则表达式的查询路由器。

    当 LLM 未启用或调用失败时，作为回退路由方案。
    通过 _ask_by_rules 和 _try_query_by_rules 两个方法实现路由。
    """

    def __init__(self, agent):
        """agent 是 DataAgent 实例，提供 df/ask/方法访问。"""
        self.agent = agent

    @property
    def df(self):
        return self.agent.df

    def ask_by_rules(self, question: str) -> str:
        """关键词/正则路由。LLM 未启用或调用失败时使用。"""
        q = question.strip().lower()

        # 自动图表 / 报告
        if any(k in q for k in ("自动图表", "自动报告", "生成报告", "auto report", "auto chart")):
            return self.agent.chart("auto")
        if any(k in q for k in ("热力图", "heatmap", "相关性图")):
            return self.agent.chart("heatmap")

        # 直方图
        hist_match = re.search(
            r"(?:画|绘制|生成)?\s*(?:直方图|histogram|hist)\s*(?:图)?\s*[:：]?\s*([\w一-龥_]+)",
            question,
        )
        if hist_match or "直方图" in q:
            col = hist_match.group(1) if hist_match else self._pick_numeric(q)
            return self.agent.chart("histogram", col) if col else "⚠️  请指定数值列名"

        # 箱线图
        box_match = re.search(
            r"(?:箱线图|boxplot)\s*[:：]?\s*([\w一-龥_]+)\s*(?:按|by|分组)?\s*([\w一-龥_]+)?",
            question,
        )
        if box_match:
            return self.agent.chart("boxplot", box_match.group(1), box_match.group(2))
        if "箱线图" in q:
            col = self._pick_numeric(q)
            return self.agent.chart("boxplot", col) if col else "⚠️  请指定数值列名"

        # 条形图 / 柱状图
        bar_match = re.search(
            r"(?:条形图|柱状图|bar|barplot)\s*[:：]?\s*([\w一-龥_]+)",
            question,
        )
        if bar_match or any(k in q for k in ("条形图", "柱状图")):
            col = bar_match.group(1) if bar_match else self._pick_categorical(q)
            return self.agent.chart("barplot", col) if col else "⚠️  请指定列名"

        # 散点图
        scatter_match = re.search(
            r"(?:散点图|scatter)\s*[:：]?\s*([\w一-龥_]+)\s*[和与,，\s]*\s*([\w一-龥_]+)",
            question,
        )
        if scatter_match or "散点图" in q:
            if scatter_match:
                return self.agent.chart("scatter", scatter_match.group(1), scatter_match.group(2))
            nums = [c for c in (self.df.columns if self.df is not None else []) if c.lower() in q]
            if len(nums) >= 2:
                return self.agent.chart("scatter", nums[0], nums[1])
            return "⚠️  请指定两个数值列，例如: 画 年龄 和 销售额 散点图"

        # 分组聚合
        group_match = re.search(
            r"(?:按|group by)\s*([\w一-龥_]+)\s*(?:聚合|分组|统计)?\s*([\w一-龥_]+)?",
            question,
        )
        if group_match and self.df is not None:
            g = group_match.group(1)
            v = group_match.group(2) or self._pick_numeric(q)
            return self.agent.groupby_agg(g, v) if v else "⚠️  请指定要聚合的数值列"

        # 异常值检测
        outlier_match = re.search(
            r"(?:异常值|outlier)\s*[:：]?\s*([\w一-龥_]+)", question,
        )
        if outlier_match or "异常值" in q:
            col = outlier_match.group(1) if outlier_match else self._pick_numeric(q)
            return self.agent.outliers(col) if col else "⚠️  请指定数值列名"

        # 数据查询
        query_reply = self._try_query_by_rules(question)
        if query_reply is not None:
            return query_reply

        # 相关性
        if any(k in q for k in ("相关", "correlation", "corr", "热力")):
            return self.agent.correlation()
        # 分类列
        if any(k in q for k in ("分类列", "categorical", "类别")):
            return self.agent.categorical()
        # 统计摘要
        if any(k in q for k in ("统计", "summary", "describe", "数值", "数字列")):
            return self.agent.summary()
        # 概览 / 完整报告
        if any(k in q for k in ("完整报告", "full report", "report", "概览", "overview", "看看", "查看数据", "info")):
            return self.agent.overview()

        return (
            f"🤖 {self.agent.name} 还没完全理解你的问题：'{question}'\n"
            f"试试这些关键词：概览 / 统计 / 相关性 / 自动图表 / 按 X 聚合 Y\n"
            f"输入 'help' 查看完整命令列表。"
        )

    # ---------- 查询解析 ----------

    def _try_query_by_rules(self, question: str) -> Optional[str]:
        """用简单规则识别查询/搜索需求。"""
        if self.df is None:
            if any(k in question for k in QUERY_TRIGGERS):
                return self.agent._no_data_msg()
            return None

        q = question.strip()
        q_lower = q.lower()
        if not any(k in q_lower for k in QUERY_TRIGGERS):
            return None

        column = self._find_mentioned_column(q_lower)

        # 比较操作符
        if column:
            for token, op in COMPARE_TOKENS:
                if token in q:
                    value = q.split(token, 1)[1].strip(QUERY_VALUE_STRIP_CHARS)
                    return self.agent.query_data(conditions=[{"column": column, "op": op, "value": value}])

            # 包含/不包含
            for token in ("不包含", "包含", "含有", "包括"):
                if token in q:
                    op = CompareOp.from_user_token(token)
                    value = q.split(token, 1)[1].strip(QUERY_VALUE_STRIP_CHARS)
                    return self.agent.query_data(conditions=[{"column": column, "op": op, "value": value}])

            # 等于
            for token in ("等于", "为", "是", "=", "=="):
                if token in q:
                    value = q.split(token, 1)[1].strip(QUERY_VALUE_STRIP_CHARS)
                    return self.agent.query_data(
                        conditions=[{"column": column, "op": "eq", "value": value}],
                        match_mode="exact",
                    )

        # 关键词搜索
        keyword = q
        for token in QUERY_TRIGGERS:
            keyword = keyword.replace(token, " ")
        keyword = keyword.strip(QUERY_VALUE_STRIP_CHARS)
        if column and keyword.startswith(str(column)):
            keyword = keyword[len(str(column)):].strip(QUERY_VALUE_STRIP_CHARS)
        return self.agent.query_data(keyword=keyword) if keyword else None

    def _find_mentioned_column(self, q: str) -> Optional[str]:
        if self.df is None:
            return None
        for c in self.df.columns:
            if str(c).lower() in q:
                return c
        return None

    def _pick_numeric(self, q: str) -> Optional[str]:
        if self.df is None:
            return None
        for c in self.df.select_dtypes(include="number").columns:
            if str(c).lower() in q:
                return c
        return None

    def _pick_categorical(self, q: str) -> Optional[str]:
        if self.df is None:
            return None
        for c in self.df.select_dtypes(exclude="number").columns:
            if str(c).lower() in q:
                return c
        return None
