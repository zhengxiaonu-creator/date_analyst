"""Agent 核心 - 命令行 & 自然语言路由。"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import List, Optional

import pandas as pd

from .constants import ChartType, CompareOp, Intent, MAX_CONVERSATION_HISTORY
from .conversation import ConversationManager
from .data_loader import DataLoader
from .analysis import DataProfiler, AdvancedAnalysis
from .visualizer import DataVisualizer

logger = logging.getLogger(__name__)

AGENT_NAME = "数据分析V0.00.04"


class DataAgent:
    """面向对话式使用的数据分析 Agent。"""

    def __init__(self, output_dir: str = "outputs"):
        self.name = AGENT_NAME
        self.output_dir = output_dir
        self.loader = DataLoader()
        self.df: Optional[pd.DataFrame] = None
        self.file_path: Optional[Path] = None
        self.file_name: Optional[str] = None
        self.profiler: Optional[DataProfiler] = None
        self.advanced: Optional[AdvancedAnalysis] = None
        self.visualizer: Optional[DataVisualizer] = None
        self.history: List[dict] = []
        self._llm_router = None  # LLMRouter 实例，延迟初始化
        self._conversation = ConversationManager()

        # 延迟导入的子模块
        self._rule_router = None
        self._intent_executor = None

    # ---------- 子模块懒加载 ----------

    @property
    def rule_router(self):
        if self._rule_router is None:
            from .router_rules import RuleRouter
            self._rule_router = RuleRouter(self)
        return self._rule_router

    @property
    def intent_executor(self):
        if self._intent_executor is None:
            from .intent_executor import IntentExecutor
            self._intent_executor = IntentExecutor(self)
        return self._intent_executor

    # ---------- 加载数据 ----------

    def set_dataframe(self, df: pd.DataFrame, file_name: Optional[str] = None) -> None:
        """基于已有 DataFrame 初始化 Agent 的分析工具。"""
        self.df = df
        self.file_name = file_name or self.file_name or "上传的数据"
        self.file_path = None
        self.profiler = DataProfiler(df)
        self.advanced = AdvancedAnalysis(df)
        self.visualizer = DataVisualizer(df, self.output_dir)
        self._record("set_dataframe", {"file": self.file_name})

    def load_file(
        self,
        file_path: Optional[str] = None,
        file_object=None,
        file_name: Optional[str] = None,
        sheet: Optional[str] = None,
    ) -> str:
        try:
            if file_object is not None:
                df = self.loader.load(file_object=file_object, file_name=file_name,
                                      sheet_name=sheet or 0)
                self.set_dataframe(df, file_name=file_name or "上传的文件")
            elif file_path is not None:
                path = Path(file_path).expanduser()
                if not path.exists():
                    return f"❌ 文件不存在: {path}"
                df = self.loader.load(file_path=path, sheet_name=sheet or 0)
                self.set_dataframe(df, file_name=path.name)
                self.file_path = path
            else:
                return "❌ 请提供文件路径或上传文件"

            info = self.profiler.basic_info()
            self._record("load", {"file": self.file_name})
            return (f"✅ 已加载文件: {self.file_name}\n"
                    f"   行数: {info['行数']}, 列数: {info['列数']}, "
                    f"缺失值: {info['缺失值总数']}, 内存: {info['内存占用(MB)']} MB")
        except FileNotFoundError as e:
            logger.warning("文件不存在: %s", e)
            return f"❌ 文件不存在: {e}"
        except ValueError as e:
            logger.warning("数据加载失败: %s", e)
            return f"❌ 数据格式错误: {e}"
        except Exception as e:
            logger.error("加载文件时出错", exc_info=True)
            return f"❌ 加载失败: {e}"

    # ---------- LLM 配置 ----------

    def configure_llm(self, api_key: str, base_url: str, model: str) -> None:
        """启用 LLM 语义路由。需要在加载数据之后调用。"""
        if self.df is None:
            logger.warning("configure_llm 在无数据时被调用，已忽略")
            return
        from .llm_router import LLMRouter
        self._llm_router = LLMRouter(api_key, base_url, model, self.df,
                                     file_name=self.file_name)
        self._conversation.clear()

    def get_conversation_history(self) -> List[dict]:
        """返回 LLM 对话历史副本。"""
        return self._conversation.get_history()

    def set_conversation_history(self, history: Optional[List[dict]]) -> None:
        """设置 LLM 对话历史。"""
        self._conversation.set_history(history)

    # ---------- 分析结果 API ----------

    def overview(self) -> str:
        if self.profiler is None:
            return self._no_data_msg()
        return self.profiler.full_report()

    def summary(self) -> str:
        if self.profiler is None:
            return self._no_data_msg()
        s = self.profiler.numeric_summary()
        if s is None:
            return "无数值列。"
        return s.to_string()

    def categorical(self) -> str:
        if self.profiler is None:
            return self._no_data_msg()
        result = self.profiler.categorical_summary()
        if not result:
            return "无分类列。"
        lines = []
        for col, df in result.items():
            lines.append(f"\n--- {col} ---")
            lines.append(df.to_string())
        return "\n".join(lines)

    def correlation(self) -> str:
        if self.profiler is None:
            return self._no_data_msg()
        c = self.profiler.correlation()
        if c is None:
            return "数值列不足两张，无法计算相关性。"
        return c.to_string()

    def groupby_agg(self, group_col: str, value_col: str) -> str:
        if self.advanced is None:
            return self._no_data_msg()
        try:
            result = self.advanced.groupby_agg(group_col, value_col)
            return f"按 {group_col} 聚合 {value_col}:\n" + result.head(15).to_string()
        except KeyError as e:
            logger.warning("分组聚合列不存在: %s", e)
            return f"❌ 列不存在: {e}"
        except Exception as e:
            logger.error("分组聚合失败", exc_info=True)
            return f"❌ 分组聚合失败: {e}"

    def outliers(self, column: str) -> str:
        if self.advanced is None:
            return self._no_data_msg()
        try:
            odf = self.advanced.outliers(column)
            return (f"列 '{column}' 的异常值 (IQR 方法): {len(odf)} 行\n"
                    + odf.head(10).to_string())
        except KeyError as e:
            logger.warning("异常值检测列不存在: %s", e)
            return f"❌ 列不存在: {e}"
        except Exception as e:
            logger.error("异常值检测失败", exc_info=True)
            return f"❌ 异常值检测失败: {e}"

    def query_data(
        self,
        keyword: Optional[str] = None,
        columns: Optional[list[str]] = None,
        conditions: Optional[list[dict]] = None,
        match_mode: str = "contains",
        case_sensitive: bool = False,
        limit: int = 20,
    ) -> str:
        """查询当前已加载数据中的原始记录。"""
        if self.advanced is None or self.df is None:
            return self._no_data_msg()

        try:
            limit = max(1, min(int(limit or 20), 100))
        except (TypeError, ValueError):
            limit = 20

        valid_columns = []
        for col in columns or []:
            actual = self._validate_column(str(col))
            if not actual:
                return f"⚠️  查询列不存在: {col}"
            valid_columns.append(actual)

        valid_conditions = []
        for condition in conditions or []:
            col = self._validate_column(str(condition.get("column", "")))
            if not col:
                return f"⚠️  查询列不存在: {condition.get('column', '')}"
            valid_conditions.append({
                "column": col,
                "op": condition.get("op", "eq"),
                "value": condition.get("value"),
            })

        if keyword in (None, "") and not valid_conditions:
            return "请提供要查询的关键词或筛选条件，例如：查找 张三，或 查询 销售额 大于 1000。"

        try:
            result, total = self.advanced.query_rows(
                conditions=valid_conditions,
                keyword=keyword,
                columns=valid_columns,
                match_mode=match_mode,
                case_sensitive=case_sensitive,
                limit=limit,
            )
        except KeyError as e:
            logger.warning("查询列不存在: %s", e)
            return f"❌ 查询失败: {e}"
        except Exception as e:
            logger.error("查询失败", exc_info=True)
            return f"❌ 查询失败: {e}"

        desc = self._format_query_desc(keyword, valid_columns, valid_conditions)
        if total == 0:
            return f"未找到匹配数据。\n查询条件：{desc}"

        return (
            f"查询结果：共匹配 {total} 行，显示前 {len(result)} 行。\n"
            f"查询条件：{desc}\n\n"
            + result.to_string(index=False)
        )

    def chart(self, chart_type: str, *args) -> str:
        if self.visualizer is None:
            return self._no_data_msg()
        try:
            mapped = ChartType.from_user_input(chart_type)
            if mapped is None:
                return self._tool_missing_msg(f"图表类型 {chart_type}")

            if mapped == ChartType.HISTOGRAM:
                return f"📉 已生成直方图 → {self.visualizer.histogram(args[0])}"
            elif mapped == ChartType.BOXPLOT:
                col = args[0]
                group_by = args[1] if len(args) > 1 else None
                return f"📦 已生成箱线图 → {self.visualizer.boxplot(col, group_by)}"
            elif mapped == ChartType.BARPLOT:
                return f"📊 已生成条形图 → {self.visualizer.barplot(args[0])}"
            elif mapped == ChartType.HEATMAP:
                path = self.visualizer.heatmap()
                return f"🗺️  已生成热力图 → {path}" if path else "⚠️  数值列不足"
            elif mapped == ChartType.SCATTER:
                return f"🔵 已生成散点图 → {self.visualizer.scatter(args[0], args[1])}"
            elif mapped == ChartType.AUTO:
                files = self.visualizer.auto_report()
                return f"📄 已生成 {len(files)} 张图表:\n" + "\n".join(f"  - {f}" for f in files)
        except (IndexError, TypeError) as e:
            logger.warning("图表参数不足: chart_type=%s, args=%s", chart_type, args)
            return f"❌ 图表参数不足: {e}"
        except Exception as e:
            logger.error("生成图表失败: chart_type=%s", chart_type, exc_info=True)
            return f"❌ 生成图表失败: {e}"

    # ---------- 自然语言路由 ----------

    def ask(self, question: str) -> str:
        q = question.strip().lower()
        if not q:
            return "请输入问题或命令。"
        if q in ("quit", "exit", "退出", "再见"):
            return "__EXIT__"
        if q in ("help", "?", "帮助", "怎么用"):
            return self._help_text()

        load_match = re.search(
            r"(?:加载|打开|load|open)\s*[\s:：]*([\w一-龥/\\.\-_]+?\.(?:csv|xlsx|xls))",
            question, re.IGNORECASE,
        )
        if load_match:
            return self.load_file(file_path=load_match.group(1))

        # 启用 LLM 时，优先让大模型理解需求并路由到已有工具。
        if self._llm_router is not None:
            reply = self._ask_llm(question)
            if not reply.startswith("__LLM_ERROR__"):
                return reply
            question = reply.replace("__LLM_ERROR__", "", 1).strip() or question

        return self.rule_router.ask_by_rules(question)

    # ---------- LLM 辅助方法 ----------

    def _ask_llm(self, question: str) -> str:
        """通过 LLM 进行语义路由并执行对应操作。"""
        result = self._llm_router.route(question, self._conversation.get_history())

        intent = result.get("intent", "error")
        params = result.get("params", {})
        commentary = result.get("commentary", "")

        if intent == "error":
            return f"__LLM_ERROR__{question}"

        # 记录对话历史
        self._conversation.append("user", question)

        if intent in (Intent.UNSUPPORTED, Intent.TOOL_MISSING):
            reply = self._tool_missing_msg(params.get("requested", question))
            self._conversation.append("assistant", reply)
            return reply

        if intent == Intent.CHAT:
            reply = commentary or "你好！我是数据分析助手，可以帮你分析数据。"
            self._conversation.append("assistant", reply)
            return reply

        exec_result = self.intent_executor.execute(intent, params)

        # 拼接 LLM 回复和执行结果
        if commentary and exec_result:
            reply = f"{commentary}\n\n{exec_result}"
        elif commentary:
            reply = commentary
        else:
            reply = exec_result

        self._conversation.append("assistant", reply)
        return reply

    # ---------- 列名校验 ----------

    def _validate_column(self, col_name: str, expected_type: Optional[str] = None) -> Optional[str]:
        """校验列名是否存在，支持模糊匹配。返回实际列名或 None。"""
        if self.df is None or not col_name:
            return None

        # 精确匹配
        if col_name in self.df.columns:
            col = col_name
        # 忽略大小写匹配
        else:
            col_map = {c.lower(): c for c in self.df.columns}
            if col_name.lower() in col_map:
                col = col_map[col_name.lower()]
            else:
                # 子串模糊匹配
                col = None
                for c in self.df.columns:
                    if col_name.lower() in c.lower() or c.lower() in col_name.lower():
                        col = c
                        break

        if col is None:
            return None

        # 校验列类型
        if expected_type == "numeric" and not pd.api.types.is_numeric_dtype(self.df[col]):
            return None
        if expected_type == "categorical" and pd.api.types.is_numeric_dtype(self.df[col]):
            return None

        return col

    # ---------- 工具方法 ----------

    @staticmethod
    def _no_data_msg() -> str:
        return "⚠️  还没有加载数据，请先上传 CSV 或 Excel 文件。"

    @staticmethod
    def _tool_missing_msg(requested: str = "") -> str:
        suffix = f"：{requested}" if requested else ""
        return f"当前功能不存在{suffix}，请在 Agent 中加入新的数据分析功能。"

    def _record(self, action: str, data: dict):
        self.history.append({"action": action, "data": data})

    def _help_text(self) -> str:
        return (
            "可用命令（可直接输入中文自然语言）：\n"
            "  📂 加载数据       → '加载 data.csv' 或 '打开 sales.xlsx'\n"
            "  📊 数据概览       → '概览' 或 '完整报告'\n"
            "  📈 统计摘要       → '统计' / 'describe'\n"
            "  🔍 查看分类       → '分类列'\n"
            "  🔗 相关性         → '相关性' / '热力图'\n"
            "  🔎 数据查询       → '查找 张三' / '查询 地区 是 华东' / '找出 销售额 大于 1000 的行'\n"
            "  🎯 分组聚合       → '按 地区 聚合 销售额'\n"
            "  📉 画图           → '画 年龄 直方图' / '画 销售额 箱线图 按 地区'\n"
            "  📄 自动图表报告   → '自动图表'\n"
            "  ⚠️  异常值         → '检测 销售额 异常值'\n"
            "  💬 帮助           → 'help' / '?'\n"
            "  🚪 退出           → '退出' / 'quit'"
        )

    @staticmethod
    def _format_query_desc(
        keyword: Optional[str],
        columns: list[str],
        conditions: list[dict],
    ) -> str:
        parts = []
        for condition in conditions:
            op = str(condition.get("op", "eq")).lower()
            col = condition.get("column")
            if op in ("isna", "notna", "is_null", "not_null"):
                parts.append(f"{col} {CompareOp.display_name(op)}")
            else:
                parts.append(f"{col} {CompareOp.display_name(op)} {condition.get('value')}")
        if keyword not in (None, ""):
            scope = f"（限定列：{', '.join(map(str, columns))}）" if columns else "（全表）"
            parts.append(f"关键词 {keyword}{scope}")
        return "；".join(parts) if parts else "无"

    # ---------- 交互式会话 ----------

    def chat(self):
        print("=" * 60)
        print(f"🤖 {self.name} - 有什么可以帮你的？")
        print("=" * 60)
        print(self._help_text())
        while True:
            try:
                user_input = input("\n🧑 你: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n👋 再见！")
                break
            if not user_input:
                continue
            reply = self.ask(user_input)
            if reply == "__EXIT__":
                print("👋 再见！")
                break
            print(f"🤖 {self.name}:")
            print(reply)
