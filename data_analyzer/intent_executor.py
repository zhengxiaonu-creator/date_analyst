"""意图执行模块 — 将 LLM 返回的意图映射到具体的分析方法。"""

from __future__ import annotations

import logging
from typing import Optional

from .constants import ChartType, Intent

logger = logging.getLogger(__name__)


class IntentExecutor:
    """根据 LLM 或规则路由返回的 intent 执行对应的分析操作。"""

    def __init__(self, agent):
        """agent 是 DataAgent 实例。"""
        self.agent = agent

    def execute(self, intent: str, params: dict) -> str:
        """将意图字符串映射到 DataAgent 的分析方法。"""
        try:
            if intent == Intent.OVERVIEW:
                return self.agent.overview()
            elif intent == Intent.SUMMARY:
                return self.agent.summary()
            elif intent == Intent.CATEGORICAL:
                return self.agent.categorical()
            elif intent == Intent.CORRELATION:
                return self.agent.correlation()
            elif intent == Intent.GROUPBY_AGG:
                return self._exec_groupby(params)
            elif intent == Intent.OUTLIERS:
                return self._exec_outliers(params)
            elif intent == Intent.CHART:
                return self._exec_chart(params)
            elif intent == Intent.QUERY_DATA:
                return self._exec_query(params)
            elif intent in (Intent.CHAT,):
                return params.get("commentary", "") or "你好！我是数据分析助手，可以帮你分析数据。"
            elif intent in (Intent.UNSUPPORTED, Intent.TOOL_MISSING):
                return self.agent._tool_missing_msg(params.get("requested", ""))
            else:
                return self.agent._tool_missing_msg(intent)
        except Exception:
            logger.error("执行 intent=%s 时出错", intent, exc_info=True)
            return f"❌ 执行 {intent} 失败，请重试或换个说法。"

    def _exec_groupby(self, params: dict) -> str:
        g = params.get("group_col", "")
        v = params.get("value_col", "")
        g = self.agent._validate_column(g, "categorical")
        v = self.agent._validate_column(v, "numeric")
        if not g or not v:
            return "⚠️  请指定有效的分组列和数值列。"
        return self.agent.groupby_agg(g, v)

    def _exec_outliers(self, params: dict) -> str:
        col = self.agent._validate_column(params.get("column", ""), "numeric")
        if not col:
            return "⚠️  请指定有效的数值列名。"
        return self.agent.outliers(col)

    def _exec_chart(self, params: dict) -> str:
        chart_type = params.get("chart_type", "auto")
        columns = params.get("columns", [])
        validated = [self.agent._validate_column(c) for c in columns]
        validated = [c for c in validated if c is not None]
        return self.agent.chart(chart_type, *validated)

    def _exec_query(self, params: dict) -> str:
        return self.agent.query_data(
            keyword=params.get("keyword"),
            columns=params.get("columns") or [],
            conditions=params.get("conditions") or [],
            match_mode=params.get("match_mode", "contains"),
            case_sensitive=bool(params.get("case_sensitive", False)),
            limit=params.get("limit", 20),
        )
