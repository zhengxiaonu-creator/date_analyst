"""Agent 核心 - 命令行 & 自然语言路由。"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional

import pandas as pd

from .data_loader import DataLoader
from .analysis import DataProfiler, AdvancedAnalysis
from .visualizer import DataVisualizer

AGENT_NAME = "数据分析V0.00.03"


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
        self._conversation_history: List[dict] = []  # LLM 对话历史

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
        except Exception as e:
            return f"❌ 加载失败: {e}"

    # ---------- LLM 配置 ----------
    def configure_llm(self, api_key: str, base_url: str, model: str) -> None:
        """启用 LLM 语义路由。需要在加载数据之后调用。"""
        if self.df is None:
            return
        from .llm_router import LLMRouter
        self._llm_router = LLMRouter(api_key, base_url, model, self.df,
                                     file_name=self.file_name)

    def get_conversation_history(self) -> List[dict]:
        """返回 LLM 对话历史副本。"""
        return list(self._conversation_history)

    def set_conversation_history(self, history: Optional[List[dict]]) -> None:
        """设置 LLM 对话历史。"""
        self._conversation_history = list(history or [])

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
        except Exception as e:
            return f"❌ 分组聚合失败: {e}"

    def outliers(self, column: str) -> str:
        if self.advanced is None:
            return self._no_data_msg()
        try:
            odf = self.advanced.outliers(column)
            return (f"列 '{column}' 的异常值 (IQR 方法): {len(odf)} 行\n"
                    + odf.head(10).to_string())
        except Exception as e:
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
        except Exception as e:
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
            chart_type = chart_type.lower()
            if chart_type in ("hist", "histogram"):
                return f"📉 已生成直方图 → {self.visualizer.histogram(args[0])}"
            if chart_type in ("box", "boxplot"):
                col = args[0]
                group_by = args[1] if len(args) > 1 else None
                return f"📦 已生成箱线图 → {self.visualizer.boxplot(col, group_by)}"
            if chart_type in ("bar", "barplot"):
                return f"📊 已生成条形图 → {self.visualizer.barplot(args[0])}"
            if chart_type in ("heatmap", "heat", "热力图"):
                path = self.visualizer.heatmap()
                return f"🗺️  已生成热力图 → {path}" if path else "⚠️  数值列不足"
            if chart_type == "scatter":
                return f"🔵 已生成散点图 → {self.visualizer.scatter(args[0], args[1])}"
            if chart_type in ("auto", "report", "自动", "自动图表"):
                files = self.visualizer.auto_report()
                return f"📄 已生成 {len(files)} 张图表:\n" + "\n".join(f"  - {f}" for f in files)
            return self._tool_missing_msg(f"图表类型 {chart_type}")
        except Exception as e:
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

        return self._ask_by_rules(question)

    def _ask_by_rules(self, question: str) -> str:
        """关键词/正则路由。LLM 未启用或调用失败时使用。"""
        q = question.strip().lower()

        if any(k in q for k in ("自动图表", "自动报告", "生成报告", "auto report", "auto chart")):
            return self.chart("auto")
        if any(k in q for k in ("热力图", "heatmap", "相关性图")):
            return self.chart("heatmap")

        hist_match = re.search(
            r"(?:画|绘制|生成)?\s*(?:直方图|histogram|hist)\s*(?:图)?\s*[:：]?\s*([\w一-龥_]+)",
            question,
        )
        if hist_match or "直方图" in q:
            col = hist_match.group(1) if hist_match else self._pick_numeric(q)
            return self.chart("histogram", col) if col else "⚠️  请指定数值列名"

        box_match = re.search(
            r"(?:箱线图|boxplot)\s*[:：]?\s*([\w一-龥_]+)\s*(?:按|by|分组)?\s*([\w一-龥_]+)?",
            question,
        )
        if box_match:
            return self.chart("boxplot", box_match.group(1), box_match.group(2))
        if "箱线图" in q:
            col = self._pick_numeric(q)
            return self.chart("boxplot", col) if col else "⚠️  请指定数值列名"

        bar_match = re.search(
            r"(?:条形图|柱状图|bar|barplot)\s*[:：]?\s*([\w一-龥_]+)",
            question,
        )
        if bar_match or any(k in q for k in ("条形图", "柱状图")):
            col = bar_match.group(1) if bar_match else self._pick_categorical(q)
            return self.chart("barplot", col) if col else "⚠️  请指定列名"

        scatter_match = re.search(
            r"(?:散点图|scatter)\s*[:：]?\s*([\w一-龥_]+)\s*[和与,，\s]*\s*([\w一-龥_]+)",
            question,
        )
        if scatter_match or "散点图" in q:
            if scatter_match:
                return self.chart("scatter", scatter_match.group(1), scatter_match.group(2))
            nums = [c for c in (self.df.columns if self.df is not None else []) if c.lower() in q]
            if len(nums) >= 2:
                return self.chart("scatter", nums[0], nums[1])
            return "⚠️  请指定两个数值列，例如: 画 年龄 和 销售额 散点图"

        group_match = re.search(
            r"(?:按|group by)\s*([\w一-龥_]+)\s*(?:聚合|分组|统计)?\s*([\w一-龥_]+)?",
            question,
        )
        if group_match and self.df is not None:
            g = group_match.group(1)
            v = group_match.group(2) or self._pick_numeric(q)
            return self.groupby_agg(g, v) if v else "⚠️  请指定要聚合的数值列"

        outlier_match = re.search(
            r"(?:异常值|outlier)\s*[:：]?\s*([\w一-龥_]+)", question,
        )
        if outlier_match or "异常值" in q:
            col = outlier_match.group(1) if outlier_match else self._pick_numeric(q)
            return self.outliers(col) if col else "⚠️  请指定数值列名"

        query_reply = self._try_query_by_rules(question)
        if query_reply is not None:
            return query_reply

        if any(k in q for k in ("相关", "correlation", "corr", "热力")):
            return self.correlation()
        if any(k in q for k in ("分类列", "categorical", "类别")):
            return self.categorical()
        if any(k in q for k in ("统计", "summary", "describe", "数值", "数字列")):
            return self.summary()
        if any(k in q for k in ("完整报告", "full report", "report", "概览", "overview", "看看", "查看数据", "info")):
            return self.overview()

        return (
            f"🤖 {self.name} 还没完全理解你的问题：'{question}'\n"
            f"试试这些关键词：概览 / 统计 / 相关性 / 自动图表 / 按 X 聚合 Y\n"
            f"输入 'help' 查看完整命令列表。"
        )

    # ---------- 辅助 ----------
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

    def _try_query_by_rules(self, question: str) -> Optional[str]:
        """用简单规则识别查询/搜索需求。"""
        if self.df is None:
            if any(k in question for k in ("查找", "查询", "搜索", "找出", "筛选", "过滤", "检索")):
                return self._no_data_msg()
            return None

        q = question.strip()
        q_lower = q.lower()
        triggers = ("查找", "查询", "搜索", "找出", "筛选", "过滤", "检索")
        if not any(k in q_lower for k in triggers):
            return None

        column = self._find_mentioned_column(q_lower)
        compare_ops = [
            ("大于等于", "gte"), ("不小于", "gte"), (">=", "gte"),
            ("小于等于", "lte"), ("不大于", "lte"), ("<=", "lte"),
            ("大于", "gt"), (">", "gt"),
            ("小于", "lt"), ("<", "lt"),
        ]
        if column:
            for token, op in compare_ops:
                if token in q:
                    value = q.split(token, 1)[1].strip(" 的数据记录行。。，,：:")
                    return self.query_data(conditions=[{"column": column, "op": op, "value": value}])

            for token, op in (("不包含", "not_contains"), ("包含", "contains"), ("含有", "contains"), ("包括", "contains")):
                if token in q:
                    value = q.split(token, 1)[1].strip(" 的数据记录行。。，,：:")
                    return self.query_data(conditions=[{"column": column, "op": op, "value": value}])

            for token in ("等于", "为", "是", "=", "=="):
                if token in q:
                    value = q.split(token, 1)[1].strip(" 的数据记录行。。，,：:")
                    return self.query_data(conditions=[{"column": column, "op": "eq", "value": value}], match_mode="exact")

        keyword = q
        for token in triggers:
            keyword = keyword.replace(token, " ")
        keyword = keyword.strip(" 的数据记录行。。，,：:")
        if column and keyword.startswith(str(column)):
            keyword = keyword[len(str(column)):].strip(" 的数据记录行。。，,：:")
        return self.query_data(keyword=keyword) if keyword else None

    def _find_mentioned_column(self, q: str) -> Optional[str]:
        if self.df is None:
            return None
        for c in self.df.columns:
            if str(c).lower() in q:
                return c
        return None

    @staticmethod
    def _format_query_desc(
        keyword: Optional[str],
        columns: list[str],
        conditions: list[dict],
    ) -> str:
        parts = []
        op_names = {
            "eq": "=", "ne": "!=", "contains": "包含", "not_contains": "不包含",
            "gt": ">", "gte": ">=", "lt": "<", "lte": "<=",
            "isna": "为空", "notna": "非空",
        }
        for condition in conditions:
            op = str(condition.get("op", "eq")).lower()
            if op in ("isna", "notna", "is_null", "not_null"):
                parts.append(f"{condition.get('column')} {op_names.get(op, op)}")
            else:
                parts.append(
                    f"{condition.get('column')} {op_names.get(op, op)} {condition.get('value')}"
                )
        if keyword not in (None, ""):
            scope = f"（限定列：{', '.join(map(str, columns))}）" if columns else "（全表）"
            parts.append(f"关键词 {keyword}{scope}")
        return "；".join(parts) if parts else "无"

    # ---------- LLM 辅助方法 ----------
    def _ask_llm(self, question: str) -> str:
        """通过 LLM 进行语义路由并执行对应操作。"""
        result = self._llm_router.route(question, self._conversation_history)

        intent = result.get("intent", "error")
        params = result.get("params", {})
        commentary = result.get("commentary", "")

        if intent == "error":
            return f"__LLM_ERROR__{question}"

        # 记录对话历史
        self._conversation_history.append({"role": "user", "content": question})

        if intent in ("unsupported", "tool_missing"):
            reply = self._tool_missing_msg(params.get("requested", question))
            self._conversation_history.append({"role": "assistant", "content": reply})
            return reply

        if intent == "chat":
            reply = commentary or "你好！我是数据分析助手，可以帮你分析数据。"
            self._conversation_history.append({"role": "assistant", "content": reply})
            return reply

        try:
            exec_result = self._execute_intent(intent, params)
        except Exception as e:
            exec_result = f"❌ 执行失败: {e}"

        # 拼接 LLM 回复和执行结果
        if commentary and exec_result:
            reply = f"{commentary}\n\n{exec_result}"
        elif commentary:
            reply = commentary
        else:
            reply = exec_result

        self._conversation_history.append({"role": "assistant", "content": reply})
        return reply

    def _execute_intent(self, intent: str, params: dict) -> str:
        """将 LLM 返回的意图映射到具体的分析方法。"""
        if intent == "overview":
            return self.overview()
        elif intent == "summary":
            return self.summary()
        elif intent == "categorical":
            return self.categorical()
        elif intent == "correlation":
            return self.correlation()
        elif intent == "groupby_agg":
            g = params.get("group_col", "")
            v = params.get("value_col", "")
            g = self._validate_column(g, "categorical")
            v = self._validate_column(v, "numeric")
            if not g or not v:
                return "⚠️  请指定有效的分组列和数值列。"
            return self.groupby_agg(g, v)
        elif intent == "outliers":
            col = self._validate_column(params.get("column", ""), "numeric")
            if not col:
                return "⚠️  请指定有效的数值列名。"
            return self.outliers(col)
        elif intent == "chart":
            chart_type = params.get("chart_type", "auto")
            columns = params.get("columns", [])
            validated = [self._validate_column(c) for c in columns]
            validated = [c for c in validated if c is not None]
            return self.chart(chart_type, *validated)
        elif intent == "query_data":
            return self.query_data(
                keyword=params.get("keyword"),
                columns=params.get("columns") or [],
                conditions=params.get("conditions") or [],
                match_mode=params.get("match_mode", "contains"),
                case_sensitive=bool(params.get("case_sensitive", False)),
                limit=params.get("limit", 20),
            )
        elif intent == "chat":
            return params.get("commentary", "") or "你好！我是数据分析助手，可以帮你分析数据。"
        elif intent in ("unsupported", "tool_missing"):
            return self._tool_missing_msg(params.get("requested", ""))
        else:
            return self._tool_missing_msg(intent)

    def _validate_column(self, col_name: str, expected_type: Optional[str] = None) -> Optional[str]:
        """校验列名是否存在，支持模糊匹配。返回实际列名或 None。"""
        if self.df is None or not col_name:
            return None

        # 精确匹配
        if col_name in self.df.columns:
            col = col_name
        # 忽略大小写匹配
        elif col_name.lower() in {c.lower(): c for c in self.df.columns}:
            col = {c.lower(): c for c in self.df.columns}[col_name.lower()]
        # 子串模糊匹配
        else:
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
