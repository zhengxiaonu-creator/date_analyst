"""data_analyzer - 数据分析Agent001 通用数据分析包。"""

from .data_loader import DataLoader, load_data
from .analysis import DataProfiler, AdvancedAnalysis
from .visualizer import DataVisualizer
from .agent import DataAgent, AGENT_NAME
from .llm_router import LLMRouter
from .router_rules import RuleRouter
from .intent_executor import IntentExecutor
from .conversation import ConversationManager
from .constants import Intent, ChartType, CompareOp

__all__ = [
    "DataLoader",
    "load_data",
    "DataProfiler",
    "AdvancedAnalysis",
    "DataVisualizer",
    "DataAgent",
    "LLMRouter",
    "RuleRouter",
    "IntentExecutor",
    "ConversationManager",
    "Intent",
    "ChartType",
    "CompareOp",
    "AGENT_NAME",
]

__version__ = "0.00.03"
