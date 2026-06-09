"""LLM 语义路由模块 — 使用 OpenAI 兼容 API 理解自然语言并路由到对应分析功能。"""

import json
import re
from typing import Optional

import pandas as pd
from openai import OpenAI


class LLMRouter:
    """基于 LLM 的自然语言意图路由器。"""

    VALID_INTENTS = {
        "overview", "summary", "categorical", "correlation",
        "groupby_agg", "outliers", "chart", "query_data", "chat", "unsupported",
    }

    def __init__(self, api_key: str, base_url: str, model: str,
                 df: pd.DataFrame, file_name: Optional[str] = None):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.df = df
        self.file_name = file_name
        self.system_prompt = self._build_system_prompt()

    # ------------------------------------------------------------------
    # 系统提示构建
    # ------------------------------------------------------------------

    def _build_system_prompt(self) -> str:
        sections = [
            self._section_role(),
            self._section_operations(),
            self._section_data_context(),
            self._section_examples(),
        ]
        return "\n\n".join(sections)

    def _section_role(self) -> str:
        return (
            "你是数据分析 Agent 的意图路由器，不是直接生成分析结论的模型。\n"
            "你的任务是先理解用户的数据分析需求，再从可用操作中选择一个 intent，"
            "由本地 Agent 工具读取完整数据并执行分析。\n\n"
            "输出格式（严格的 JSON，不要包含 Markdown 或其他文字）：\n"
            '{"intent": "<intent_name>", "params": {...}, "commentary": "<中文简短回复>"}\n\n'
            "规则：\n"
            "- intent 必须是以下之一：overview / summary / categorical / correlation / groupby_agg / outliers / chart / query_data / chat / unsupported\n"
            "- params 中的列名必须尽量使用数据集中的原始列名\n"
            "- commentary 用中文简要说明你将要调用哪个已有工具\n"
            "- 你不能编造不存在的工具、算法、图表或分析结果\n"
            "- 如果用户请求的功能不在可用操作列表中，必须返回 unsupported\n"
            "- unsupported 的格式必须是："
            '{"intent": "unsupported", "params": {"requested": "<用户想做的功能>"}, '
            '"commentary": "当前功能不存在，请在 Agent 中加入新的数据分析功能。"}\n'
            "- 如果用户只是闲聊或打招呼，intent 设为 chat"
        )

    def _section_operations(self) -> str:
        return (
            "可用操作：\n\n"
            "1. overview — 数据概览/完整报告\n"
            "   params: {}\n\n"
            "2. summary — 数值列统计摘要（均值、标准差等）\n"
            "   params: {}\n\n"
            "3. categorical — 分类列统计（频率、唯一值等）\n"
            "   params: {}\n\n"
            "4. correlation — 列间相关性分析\n"
            "   params: {}\n\n"
            "5. groupby_agg — 按分组列聚合数值列\n"
            '   params: {"group_col": "<分类列名>", "value_col": "<数值列名>"}\n\n'
            "6. outliers — 异常值检测（IQR 方法）\n"
            '   params: {"column": "<数值列名>"}\n\n'
            "7. chart — 绘制图表\n"
            '   params: {"chart_type": "histogram|boxplot|barplot|scatter|heatmap|auto", "columns": ["<列名>", ...]}\n'
            "   - histogram: 1 个数值列\n"
            "   - boxplot: 1 个数值列，可选 1 个分组列\n"
            "   - barplot: 1 个分类列\n"
            "   - scatter: 2 个数值列 (x, y)\n"
            "   - heatmap / auto: 无需指定列\n\n"
            "8. query_data — 查询/查找/搜索当前已加载数据中的行\n"
            '   params: {"keyword": "<要搜索的关键词，可为空>", "columns": ["<限定搜索列名，可为空>"], '
            '"conditions": [{"column": "<列名>", "op": "eq|ne|contains|not_contains|gt|gte|lt|lte|isna|notna", "value": "<值>"}], '
            '"match_mode": "contains|exact", "case_sensitive": false, "limit": 20}\n'
            "   - 用户说查找/查询/搜索/找出/筛选/过滤记录时，优先使用 query_data\n"
            "   - 只给一个值时使用 keyword 全表搜索；指定列和值时使用 conditions\n"
            "   - 不要直接回答数据是否存在，必须由本地 Agent 查询完整 DataFrame\n\n"
            "9. chat — 闲聊/使用说明，不做数据分析\n"
            "   params: {}\n\n"
            "10. unsupported — 用户请求的数据分析功能当前 Agent 没有对应工具\n"
            '   params: {"requested": "<简短描述用户请求>"}\n'
            "   必须用于：预测建模、机器学习训练、回归建模、聚类、时间序列预测、"
            "外部数据库查询、多文件 join/merge、自动清洗并覆盖原始数据、生成 Word/PPT 报告等当前未列出的功能。"
        )

    def _section_data_context(self) -> str:
        lines = ["当前数据集信息："]
        if self.file_name:
            lines.append(f"- 文件: {self.file_name}")
        lines.append(f"- 行数: {len(self.df)}, 列数: {len(self.df.columns)}")

        numeric_cols = [str(c) for c in self.df.select_dtypes(include="number").columns]
        categorical_cols = [str(c) for c in self.df.select_dtypes(exclude="number").columns]
        lines.append(f"- 数值列: {', '.join(numeric_cols) if numeric_cols else '无'}")
        lines.append(f"- 分类/非数值列: {', '.join(categorical_cols) if categorical_cols else '无'}")
        lines.append("- 列信息：")
        for col in self.df.columns:
            dtype = str(self.df[col].dtype)
            null_count = int(self.df[col].isna().sum())
            unique_count = int(self.df[col].nunique())
            sample_vals = self.df[col].dropna().head(3).tolist()
            sample_str = ", ".join(str(v) for v in sample_vals)
            lines.append(
                f"  * {col} (类型: {dtype}, 缺失: {null_count}, "
                f"唯一值: {unique_count}) 示例: {sample_str}"
            )
        return "\n".join(lines)

    def _section_examples(self) -> str:
        return (
            "示例：\n\n"
            '用户: "画一下年龄的分布"\n'
            '{"intent": "chart", "params": {"chart_type": "histogram", "columns": ["年龄"]}, '
            '"commentary": "我将调用直方图工具查看年龄分布。"}\n\n'
            '用户: "各地区销售额的平均值"\n'
            '{"intent": "groupby_agg", "params": {"group_col": "地区", "value_col": "销售额"}, '
            '"commentary": "我将调用分组聚合工具按地区统计销售额。"}\n\n'
            '用户: "有没有什么异常的数据"\n'
            '{"intent": "outliers", "params": {"column": "销售额"}, '
            '"commentary": "我将调用异常值检测工具检查销售额。"}\n\n'
            '用户: "查找 张三"\n'
            '{"intent": "query_data", "params": {"keyword": "张三", "columns": [], "conditions": [], "match_mode": "contains", "case_sensitive": false, "limit": 20}, '
            '"commentary": "我将调用数据查询工具在当前数据中搜索张三。"}\n\n'
            '用户: "查询地区是华东的数据"\n'
            '{"intent": "query_data", "params": {"keyword": null, "columns": [], "conditions": [{"column": "地区", "op": "eq", "value": "华东"}], "match_mode": "exact", "case_sensitive": false, "limit": 20}, '
            '"commentary": "我将调用数据查询工具筛选地区为华东的记录。"}\n\n'
            '用户: "找出销售额大于1000的行"\n'
            '{"intent": "query_data", "params": {"keyword": null, "columns": [], "conditions": [{"column": "销售额", "op": "gt", "value": 1000}], "match_mode": "contains", "case_sensitive": false, "limit": 20}, '
            '"commentary": "我将调用数据查询工具筛选销售额大于1000的记录。"}\n\n'
            '用户: "帮我训练一个模型预测下个月销售额"\n'
            '{"intent": "unsupported", "params": {"requested": "训练模型预测下个月销售额"}, '
            '"commentary": "当前功能不存在，请在 Agent 中加入新的数据分析功能。"}\n\n'
            '用户: "你好"\n'
            '{"intent": "chat", "params": {}, '
            '"commentary": "你好！我是数据分析助手，可以帮你分析数据。试试问我数据概览、统计信息、画图表等。"}\n\n'
            '用户: "帮我看看数据有什么特点"\n'
            '{"intent": "overview", "params": {}, '
            '"commentary": "我将调用数据概览工具生成完整报告。"}'
        )

    # ------------------------------------------------------------------
    # 路由主方法
    # ------------------------------------------------------------------

    def route(self, question: str, history: Optional[list] = None) -> dict:
        """调用 LLM 进行意图路由，返回 {"intent": str, "params": dict, "commentary": str}。"""
        messages = [{"role": "system", "content": self.system_prompt}]

        # 包含最近 3 轮对话历史，支持追问
        if history:
            for turn in history[-6:]:
                messages.append(turn)

        messages.append({"role": "user", "content": question})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1,
                max_tokens=500,
                timeout=15.0,
            )
            raw = response.choices[0].message.content or ""
            return self._parse_response(raw)
        except Exception as e:
            return {"intent": "error", "params": {}, "commentary": f"LLM 调用失败: {e}"}

    # ------------------------------------------------------------------
    # 响应解析
    # ------------------------------------------------------------------

    def _parse_response(self, raw: str) -> dict:
        text = raw.strip()

        # 去除 markdown 代码围栏
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)

        # 第一级：直接解析
        try:
            result = json.loads(text)
        except json.JSONDecodeError:
            # 第二级：提取首个完整 JSON 对象，支持嵌套 params
            json_text = self._extract_json_object(text)
            if not json_text:
                return {"intent": "error", "params": {}, "commentary": "LLM 返回格式无法解析"}
            try:
                result = json.loads(json_text)
            except json.JSONDecodeError:
                return {"intent": "error", "params": {}, "commentary": "LLM 返回格式无法解析"}

        # 校验字段
        intent = result.get("intent", "error")
        params = result.get("params", {})
        commentary = result.get("commentary", "")

        if not isinstance(params, dict):
            params = {}

        if intent not in self.VALID_INTENTS:
            return {
                "intent": "unsupported",
                "params": {"requested": str(intent)},
                "commentary": "当前功能不存在，请在 Agent 中加入新的数据分析功能。",
            }

        return {"intent": intent, "params": params, "commentary": commentary}

    @staticmethod
    def _extract_json_object(text: str) -> Optional[str]:
        start = text.find("{")
        if start < 0:
            return None

        depth = 0
        in_string = False
        escape = False
        for i in range(start, len(text)):
            ch = text[i]
            if escape:
                escape = False
                continue
            if ch == "\\" and in_string:
                escape = True
                continue
            if ch == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start:i + 1]
        return None
