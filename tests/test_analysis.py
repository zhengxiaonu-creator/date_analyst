"""测试 AdvancedAnalysis.query_rows — 各种条件组合。"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data_analyzer.analysis import AdvancedAnalysis


@pytest.fixture
def sample_df():
    """创建测试用 DataFrame。"""
    return pd.DataFrame({
        "姓名": ["张三", "李四", "王五", "赵六", "孙七"],
        "年龄": [25, 30, 22, 35, 28],
        "城市": ["北京", "上海", "北京", "广州", "深圳"],
        "销售额": [1000, 2000, 1500, 800, 3000],
    })


class TestQueryRows:
    """AdvancedAnalysis.query_rows 测试。"""

    def test_keyword_search(self, sample_df):
        """全表关键词搜索。"""
        adv = AdvancedAnalysis(sample_df)
        result, total = adv.query_rows(keyword="张三")
        assert total == 1
        assert result.iloc[0]["姓名"] == "张三"

    def test_keyword_search_case_insensitive(self, sample_df):
        """不区分大小写的关键词搜索。"""
        adv = AdvancedAnalysis(sample_df)
        # 中文不区分大小写测试：用城市搜索
        result, total = adv.query_rows(keyword="北京", case_sensitive=False)
        assert total == 2

    def test_condition_eq(self, sample_df):
        """等于条件筛选。"""
        adv = AdvancedAnalysis(sample_df)
        result, total = adv.query_rows(
            conditions=[{"column": "城市", "op": "eq", "value": "北京"}]
        )
        assert total == 2

    def test_condition_gt(self, sample_df):
        """大于条件筛选。"""
        adv = AdvancedAnalysis(sample_df)
        result, total = adv.query_rows(
            conditions=[{"column": "销售额", "op": "gt", "value": 1000}]
        )
        assert total == 3  # 2000, 1500, 3000
        assert all(r > 1000 for r in result["销售额"])

    def test_condition_gte(self, sample_df):
        """大于等于条件筛选。"""
        adv = AdvancedAnalysis(sample_df)
        result, total = adv.query_rows(
            conditions=[{"column": "销售额", "op": "gte", "value": 1000}]
        )
        assert total == 4  # 1000, 2000, 1500, 3000

    def test_condition_lt(self, sample_df):
        """小于条件筛选。"""
        adv = AdvancedAnalysis(sample_df)
        result, total = adv.query_rows(
            conditions=[{"column": "年龄", "op": "lt", "value": 30}]
        )
        assert total == 3  # 25, 22, 28

    def test_condition_contains(self, sample_df):
        """包含条件筛选。"""
        adv = AdvancedAnalysis(sample_df)
        result, total = adv.query_rows(
            conditions=[{"column": "城市", "op": "contains", "value": "海"}]
        )
        assert total == 1
        assert result.iloc[0]["城市"] == "上海"

    def test_condition_isna(self, sample_df):
        """为空条件筛选。"""
        df = sample_df.copy()
        df.loc[0, "姓名"] = None
        adv = AdvancedAnalysis(df)
        result, total = adv.query_rows(
            conditions=[{"column": "姓名", "op": "isna", "value": ""}]
        )
        assert total == 1

    def test_condition_notna(self, sample_df):
        """非空条件筛选。"""
        df = sample_df.copy()
        df.loc[0, "姓名"] = None
        adv = AdvancedAnalysis(df)
        result, total = adv.query_rows(
            conditions=[{"column": "姓名", "op": "notna", "value": ""}]
        )
        assert total == 4

    def test_combined_keyword_and_condition(self, sample_df):
        """关键词 + 条件组合（交集）。"""
        adv = AdvancedAnalysis(sample_df)
        result, total = adv.query_rows(
            keyword="张三",
            conditions=[{"column": "年龄", "op": "gt", "value": 20}],
        )
        assert total == 1

    def test_sort_by(self, sample_df):
        """排序功能。"""
        adv = AdvancedAnalysis(sample_df)
        result, total = adv.query_rows(
            sort_by="销售额",
            ascending=False,
        )
        assert result.iloc[0]["销售额"] == 3000
        assert result.iloc[-1]["销售额"] == 800

    def test_limit(self, sample_df):
        """limit 截断。"""
        adv = AdvancedAnalysis(sample_df)
        result, total = adv.query_rows(limit=2)
        assert len(result) == 2
        assert total == 5

    def test_nonexistent_column_raises(self, sample_df):
        """不存在的列名应抛出 KeyError。"""
        adv = AdvancedAnalysis(sample_df)
        with pytest.raises(KeyError, match="查询列不存在"):
            adv.query_rows(conditions=[{"column": "不存在", "op": "eq", "value": "x"}])


class TestSearchRows:
    """search_rows 方法测试（query_rows 的别名）。"""

    def test_search_rows(self, sample_df):
        adv = AdvancedAnalysis(sample_df)
        result, total = adv.search_rows(keyword="北京")
        assert total == 2
