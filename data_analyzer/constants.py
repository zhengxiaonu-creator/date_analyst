"""常量定义 — 意图、图表类型、比较操作符等枚举常量。

用于 agent.py、llm_router.py、app.py 等模块，避免裸字符串散落。
"""

from __future__ import annotations

from enum import Enum


# ============================================================
# 意图类型
# ============================================================

class Intent(str, Enum):
    """LLM 语义路由支持的意图。"""
    OVERVIEW = "overview"
    SUMMARY = "summary"
    CATEGORICAL = "categorical"
    CORRELATION = "correlation"
    GROUPBY_AGG = "groupby_agg"
    OUTLIERS = "outliers"
    CHART = "chart"
    QUERY_DATA = "query_data"
    CHAT = "chat"
    UNSUPPORTED = "unsupported"
    TOOL_MISSING = "tool_missing"
    ERROR = "error"

    @classmethod
    def valid_intents(cls) -> set[str]:
        """返回 LLM 可路由的合法意图集。"""
        return {cls.OVERVIEW, cls.SUMMARY, cls.CATEGORICAL, cls.CORRELATION,
                cls.GROUPBY_AGG, cls.OUTLIERS, cls.CHART, cls.QUERY_DATA,
                cls.CHAT, cls.UNSUPPORTED}


# ============================================================
# 图表类型
# ============================================================

class ChartType(str, Enum):
    """DataVisualizer 支持的图表类型。"""
    HISTOGRAM = "histogram"
    BOXPLOT = "boxplot"
    BARPLOT = "barplot"
    SCATTER = "scatter"
    HEATMAP = "heatmap"
    AUTO = "auto"

    @classmethod
    def from_user_input(cls, text: str) -> str | None:
        """将用户输入映射到标准图表类型。"""
        t = text.lower().strip()
        mapping: dict[str, str] = {
            "hist": cls.HISTOGRAM, "histogram": cls.HISTOGRAM,
            "直方图": cls.HISTOGRAM,
            "box": cls.BOXPLOT, "boxplot": cls.BOXPLOT,
            "箱线图": cls.BOXPLOT,
            "bar": cls.BARPLOT, "barplot": cls.BARPLOT,
            "条形图": cls.BARPLOT, "柱状图": cls.BARPLOT,
            "scatter": cls.SCATTER, "散点图": cls.SCATTER,
            "heatmap": cls.HEATMAP, "heat": cls.HEATMAP,
            "热力图": cls.HEATMAP, "相关性图": cls.HEATMAP,
            "auto": cls.AUTO, "report": cls.AUTO,
            "自动": cls.AUTO, "自动图表": cls.AUTO,
        }
        return mapping.get(t)


# ============================================================
# 比较操作符
# ============================================================

class CompareOp(str, Enum):
    """AdvancedAnalysis.query_rows 支持的比较操作符。"""
    EQ = "eq"
    NE = "ne"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    ISNA = "isna"
    NOTNA = "notna"

    @classmethod
    def display_name(cls, op: str) -> str:
        """返回操作符的中文显示名。"""
        names: dict[str, str] = {
            cls.EQ: "等于",
            cls.NE: "不等于",
            cls.CONTAINS: "包含",
            cls.NOT_CONTAINS: "不包含",
            cls.GT: "大于",
            cls.GTE: "大于等于",
            cls.LT: "小于",
            cls.LTE: "小于等于",
            cls.ISNA: "为空",
            cls.NOTNA: "非空",
        }
        return names.get(op, op)

    @classmethod
    def from_user_token(cls, token: str) -> str | None:
        """将中文/符号 token 映射到操作符。"""
        mapping: dict[str, str] = {
            "等于": cls.EQ, "为": cls.EQ, "是": cls.EQ,
            "=": cls.EQ, "==": cls.EQ,
            "不等于": cls.NE, "!=": cls.NE,
            "包含": cls.CONTAINS, "含有": cls.CONTAINS, "包括": cls.CONTAINS,
            "不包含": cls.NOT_CONTAINS,
            "大于": cls.GT, ">": cls.GT,
            "大于等于": cls.GTE, "不小于": cls.GTE, ">=": cls.GTE,
            "小于": cls.LT, "<": cls.LT,
            "小于等于": cls.LTE, "不大于": cls.LTE, "<=": cls.LTE,
        }
        return mapping.get(token)


# ============================================================
# 查询触发关键词
# ============================================================

QUERY_TRIGGERS: tuple[str, ...] = (
    "查找", "查询", "搜索", "找出", "筛选", "过滤", "检索",
)

# 查询结果尾部需要清理的字符
QUERY_VALUE_STRIP_CHARS: str = " 的数据记录行。。，,：:"

# 比较操作符（按优先级排序，长 token 在前）
COMPARE_TOKENS: list[tuple[str, str]] = [
    ("大于等于", CompareOp.GTE), ("不小于", CompareOp.GTE), (">=", CompareOp.GTE),
    ("小于等于", CompareOp.LTE), ("不大于", CompareOp.LTE), ("<=", CompareOp.LTE),
    ("大于", CompareOp.GT), (">", CompareOp.GT),
    ("小于", CompareOp.LT), ("<", CompareOp.LT),
]

# ============================================================
# 对话历史
# ============================================================

MAX_CONVERSATION_HISTORY: int = 20  # 最多保留 N 条消息（user+assistant 各算 1 条）

# ============================================================
# LLM 默认值
# ============================================================

DEFAULT_LLM_TIMEOUT: float = 15.0
DEFAULT_LLM_MAX_RETRIES: int = 2
DEFAULT_LLM_BASE_URL: str = "https://api.openai.com/v1"
DEFAULT_LLM_MODEL: str = "gpt-4o-mini"
