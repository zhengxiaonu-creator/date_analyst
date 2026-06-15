"""测试 LLMRouter._parse_response — JSON 提取和解析。"""

from pathlib import Path

import pandas as pd
import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data_analyzer.llm_router import LLMRouter


@pytest.fixture
def router():
    """创建最小化 LLMRouter 实例（不调用 API）。"""
    df = pd.DataFrame({"姓名": ["张三"], "年龄": [25]})
    return LLMRouter(
        api_key="sk-test",
        base_url="https://api.openai.com/v1",
        model="gpt-4o-mini",
        df=df,
        file_name="test.csv",
    )


class TestParseResponse:
    """_parse_response JSON 解析测试。"""

    def test_parse_valid_json(self, router):
        """解析合法 JSON。"""
        result = router._parse_response(
            '{"intent": "overview", "params": {}, "commentary": "查看概览"}'
        )
        assert result["intent"] == "overview"
        assert result["params"] == {}
        assert result["commentary"] == "查看概览"

    def test_parse_json_with_markdown_fence(self, router):
        """解析带 markdown 代码围栏的 JSON。"""
        result = router._parse_response(
            '```json\n{"intent": "summary", "params": {}, "commentary": "统计"}\n```'
        )
        assert result["intent"] == "summary"

    def test_parse_json_with_extra_text(self, router):
        """JSON 周围有额外文本时仍能提取。"""
        result = router._parse_response(
            '好的，我来分析一下。\n{"intent": "correlation", "params": {}, "commentary": "相关性"}\n还需要什么？'
        )
        assert result["intent"] == "correlation"

    def test_parse_json_with_nested_params(self, router):
        """解析嵌套 params 的 JSON。"""
        result = router._parse_response(
            '{"intent": "groupby_agg", "params": {"group_col": "城市", "value_col": "销售额"}, "commentary": "分组聚合"}'
        )
        assert result["intent"] == "groupby_agg"
        assert result["params"]["group_col"] == "城市"
        assert result["params"]["value_col"] == "销售额"

    def test_parse_invalid_json(self, router):
        """无效 JSON 返回 error intent。"""
        result = router._parse_response("这不是 JSON")
        assert result["intent"] == "error"

    def test_parse_empty_string(self, router):
        """空字符串返回 error intent。"""
        result = router._parse_response("")
        assert result["intent"] == "error"

    def test_parse_unknown_intent(self, router):
        """未知 intent 自动转为 unsupported。"""
        result = router._parse_response(
            '{"intent": "train_model", "params": {}, "commentary": "训练模型"}'
        )
        assert result["intent"] == "unsupported"

    def test_parse_params_not_dict(self, router):
        """params 不是 dict 时自动转为空 dict。"""
        result = router._parse_response(
            '{"intent": "overview", "params": "not_a_dict", "commentary": "test"}'
        )
        assert result["params"] == {}

    def test_extract_json_with_escaped_quotes(self, router):
        """提取含转义引号的 JSON。"""
        text = '{"intent": "chat", "params": {}, "commentary": "你好，我是数据分析助手"}'
        result = router._parse_response(text)
        assert result["intent"] == "chat"

    def test_extract_nested_braces(self, router):
        """提取嵌套花括号的 JSON。"""
        text = '{"intent": "chart", "params": {"chart_type": "histogram", "columns": ["年龄"]}, "commentary": "画直方图"}'
        result = router._parse_response(text)
        assert result["intent"] == "chart"
        assert result["params"]["chart_type"] == "histogram"
        assert result["params"]["columns"] == ["年龄"]
