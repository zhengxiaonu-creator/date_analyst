"""测试 DataAgent 核心功能。"""

from pathlib import Path

import pandas as pd
import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data_analyzer.agent import DataAgent


@pytest.fixture
def agent_with_data():
    """创建带测试数据的 Agent。"""
    agent = DataAgent()
    df = pd.DataFrame({
        "姓名": ["张三", "李四", "王五"],
        "年龄": [25, 30, 22],
        "城市": ["北京", "上海", "北京"],
        "销售额": [1000, 2000, 1500],
    })
    agent.set_dataframe(df, file_name="test.csv")
    return agent


class TestValidateColumn:
    """_validate_column 三级模糊匹配测试。"""

    def test_exact_match(self, agent_with_data):
        """精确匹配。"""
        result = agent_with_data._validate_column("姓名")
        assert result == "姓名"

    def test_case_insensitive_match(self, agent_with_data):
        """忽略大小写匹配。"""
        # 模拟英文列名
        agent = DataAgent()
        df = pd.DataFrame({"UserName": ["a"], "Age": [1]})
        agent.set_dataframe(df)
        result = agent._validate_column("username")
        assert result == "UserName"

    def test_substring_fuzzy_match(self, agent_with_data):
        """子串模糊匹配。"""
        result = agent_with_data._validate_column("销售")
        assert result == "销售额"

    def test_reverse_substring_match(self, agent_with_data):
        """反向子串匹配（列名是查询的子串）。"""
        result = agent_with_data._validate_column("销售额总额")
        assert result == "销售额"

    def test_no_match_returns_none(self, agent_with_data):
        """无匹配返回 None。"""
        result = agent_with_data._validate_column("不存在")
        assert result is None

    def test_numeric_type_check(self, agent_with_data):
        """数值类型校验。"""
        result = agent_with_data._validate_column("年龄", expected_type="numeric")
        assert result == "年龄"

    def test_numeric_type_check_fails(self, agent_with_data):
        """非数值列要求 numeric 应返回 None。"""
        result = agent_with_data._validate_column("姓名", expected_type="numeric")
        assert result is None

    def test_categorical_type_check(self, agent_with_data):
        """分类类型校验。"""
        result = agent_with_data._validate_column("城市", expected_type="categorical")
        assert result == "城市"


class TestDataAgentAsk:
    """DataAgent.ask() 自然语言路由测试。"""

    def test_ask_overview(self, agent_with_data):
        """ask('概览') 返回完整报告。"""
        reply = agent_with_data.ask("概览")
        assert "基本概览" in reply
        assert "行数" in reply

    def test_ask_summary(self, agent_with_data):
        """ask('统计') 返回数值摘要。"""
        reply = agent_with_data.ask("统计")
        assert "年龄" in reply or "销售额" in reply

    def test_ask_correlation(self, agent_with_data):
        """ask('相关性') 返回相关性矩阵。"""
        reply = agent_with_data.ask("相关性")
        assert "年龄" in reply

    def test_ask_query(self, agent_with_data):
        """ask('查找 张三') 返回查询结果。"""
        reply = agent_with_data.ask("查找 张三")
        assert "张三" in reply

    def test_ask_groupby(self, agent_with_data):
        """ask('按 城市 聚合 销售额') 返回分组结果。"""
        reply = agent_with_data.ask("按 城市 聚合 销售额")
        assert "城市" in reply or "聚合" in reply

    def test_ask_help(self, agent_with_data):
        """ask('help') 返回帮助文本。"""
        reply = agent_with_data.ask("help")
        assert "可用命令" in reply

    def test_ask_empty(self, agent_with_data):
        """空问题返回提示。"""
        reply = agent_with_data.ask("")
        assert "请输入" in reply

    def test_ask_no_data(self):
        """无数据时询问应返回提示。"""
        agent = DataAgent()
        reply = agent.ask("概览")
        assert "还没有加载数据" in reply


class TestDataAgentMethods:
    """DataAgent 分析方法直接调用测试。"""

    def test_overview(self, agent_with_data):
        reply = agent_with_data.overview()
        assert "基本概览" in reply

    def test_summary(self, agent_with_data):
        reply = agent_with_data.summary()
        assert "年龄" in reply

    def test_correlation(self, agent_with_data):
        reply = agent_with_data.correlation()
        assert "年龄" in reply

    def test_outliers(self, agent_with_data):
        reply = agent_with_data.outliers("年龄")
        assert "异常值" in reply

    def test_query_data_keyword(self, agent_with_data):
        reply = agent_with_data.query_data(keyword="北京")
        assert "匹配" in reply

    def test_query_data_condition(self, agent_with_data):
        reply = agent_with_data.query_data(
            conditions=[{"column": "销售额", "op": "gt", "value": 1200}]
        )
        assert "匹配" in reply


class TestNoData:
    """无数据加载时的行为测试。"""

    def test_overview_no_data(self):
        agent = DataAgent()
        assert "还没有加载数据" in agent.overview()

    def test_query_no_data(self):
        agent = DataAgent()
        assert "还没有加载数据" in agent.query_data(keyword="test")

    def test_chart_no_data(self):
        agent = DataAgent()
        assert "还没有加载数据" in agent.chart("histogram", "col1")
