"""数据概览与统计分析模块。"""

from __future__ import annotations

from typing import Dict, Optional

import numpy as np
import pandas as pd


class DataProfiler:
    """对 DataFrame 进行全面的统计概览。"""

    def __init__(self, df: pd.DataFrame):
        if not isinstance(df, pd.DataFrame):
            raise TypeError("df 必须是 pandas.DataFrame")
        self.df = df.copy()

    def basic_info(self) -> Dict:
        df = self.df
        memory_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
        return {
            "行数": int(len(df)),
            "列数": int(len(df.columns)),
            "缺失值总数": int(df.isna().sum().sum()),
            "重复行数": int(df.duplicated().sum()),
            "内存占用(MB)": round(memory_mb, 2),
            "列名": list(df.columns),
        }

    def data_types(self) -> pd.DataFrame:
        df = self.df
        return pd.DataFrame(
            {
                "列名": df.columns,
                "数据类型": [str(d) for d in df.dtypes],
                "非空数量": df.notna().sum().values,
                "缺失数量": df.isna().sum().values,
                "缺失率(%)": (df.isna().mean() * 100).round(2).values,
                "唯一值数量": df.nunique().values,
            }
        )

    def numeric_summary(self) -> Optional[pd.DataFrame]:
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) == 0:
            return None
        stats = self.df[numeric_cols].describe(percentiles=[0.25, 0.5, 0.75, 0.95]).T
        stats["缺失数"] = self.df[numeric_cols].isna().sum()
        stats["缺失率(%)"] = (self.df[numeric_cols].isna().mean() * 100).round(2)
        return stats.round(4)

    def categorical_summary(self, top_n: int = 5) -> Dict[str, pd.DataFrame]:
        cat_cols = self.df.select_dtypes(exclude=[np.number]).columns
        result: Dict[str, pd.DataFrame] = {}
        for col in cat_cols:
            counts = self.df[col].value_counts(dropna=False).head(top_n)
            pct = (self.df[col].value_counts(normalize=True, dropna=False) * 100).round(2).head(top_n)
            result[col] = pd.DataFrame({"计数": counts, "占比(%)": pct})
        return result

    def correlation(self, method: str = "pearson") -> Optional[pd.DataFrame]:
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) < 2:
            return None
        return self.df[numeric_cols].corr(method=method).round(4)

    def full_report(self) -> str:
        lines = ["=" * 60, "📊 数据分析报告", "=" * 60, ""]
        info = self.basic_info()
        lines.append("【基本概览】")
        for k, v in info.items():
            if k == "列名":
                lines.append(f"  {k}: {', '.join(map(str, v))}")
            else:
                lines.append(f"  {k}: {v}")
        lines.append("")
        lines.append("【列信息】")
        lines.append(self.data_types().to_string(index=False))
        lines.append("")
        num_sum = self.numeric_summary()
        if num_sum is not None:
            lines.append("【数值列统计】")
            lines.append(num_sum.to_string())
            lines.append("")
        cat_sum = self.categorical_summary()
        if cat_sum:
            lines.append("【分类列统计】")
            for col, df in cat_sum.items():
                lines.append(f"  - {col}:")
                for idx, row in df.iterrows():
                    lines.append(f"      {idx}: {int(row['计数'])} ({row['占比(%)']}%)")
            lines.append("")
        corr = self.correlation()
        if corr is not None:
            lines.append("【相关性矩阵 (Pearson)】")
            lines.append(corr.to_string())
            lines.append("")
        lines.append("=" * 60)
        return "\n".join(lines)


class AdvancedAnalysis:
    """高级分析工具集。"""

    def __init__(self, df: pd.DataFrame):
        self.df = df

    def groupby_agg(
        self, group_col: str, value_col: str,
        agg_funcs: Optional[list] = None,
    ) -> pd.DataFrame:
        if group_col not in self.df.columns:
            raise KeyError(f"分组列不存在: {group_col}")
        if value_col not in self.df.columns:
            raise KeyError(f"聚合列不存在: {value_col}")
        agg_funcs = agg_funcs or ["count", "mean", "median", "min", "max", "std"]
        return self.df.groupby(group_col)[value_col].agg(agg_funcs).round(4).sort_values(
            "mean" if "mean" in agg_funcs else agg_funcs[0], ascending=False
        )

    def outliers(self, column: str, method: str = "iqr") -> pd.DataFrame:
        if column not in self.df.select_dtypes(include=[np.number]).columns:
            raise KeyError(f"列 '{column}' 不是数值列")
        s = self.df[column].dropna()
        if method == "iqr":
            q1, q3 = s.quantile(0.25), s.quantile(0.75)
            iqr = q3 - q1
            lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
            mask = (self.df[column] < lower) | (self.df[column] > upper)
        elif method == "zscore":
            z = (s - s.mean()) / s.std()
            mask = (z.abs() > 3).reindex(self.df.index, fill_value=False)
        else:
            raise ValueError("method 必须是 'iqr' 或 'zscore'")
        return self.df[mask]

    def query_rows(
        self,
        conditions: Optional[list[dict]] = None,
        keyword: Optional[str] = None,
        columns: Optional[list[str]] = None,
        match_mode: str = "contains",
        case_sensitive: bool = False,
        limit: Optional[int] = 20,
        sort_by: Optional[str] = None,
        ascending: bool = True,
    ) -> tuple[pd.DataFrame, int]:
        """按条件或关键词查询原始行，返回结果和匹配总数。"""
        if limit is not None:
            limit = max(1, min(int(limit or 20), 1000))
        match_mode = "exact" if match_mode == "exact" else "contains"
        result = self.df

        for condition in conditions or []:
            col = condition.get("column")
            op = str(condition.get("op", "eq")).lower()
            value = condition.get("value")
            if col not in result.columns:
                raise KeyError(f"查询列不存在: {col}")
            result = result[self._condition_mask(result[col], op, value, case_sensitive)]

        if keyword not in (None, ""):
            search_cols = columns or list(result.columns)
            missing = [c for c in search_cols if c not in result.columns]
            if missing:
                raise KeyError(f"查询列不存在: {', '.join(map(str, missing))}")
            mask = self._keyword_mask(result, str(keyword), search_cols, match_mode, case_sensitive)
            result = result[mask]

        if sort_by:
            if sort_by not in result.columns:
                raise KeyError(f"排序列不存在: {sort_by}")
            result = result.sort_values(by=sort_by, ascending=ascending, na_position="last")

        total = len(result)
        return (result if limit is None else result.head(limit)), total

    def search_rows(
        self,
        keyword: str,
        columns: Optional[list[str]] = None,
        match_mode: str = "contains",
        case_sensitive: bool = False,
        limit: Optional[int] = 20,
        sort_by: Optional[str] = None,
        ascending: bool = True,
    ) -> tuple[pd.DataFrame, int]:
        """在指定列或全表中搜索关键词。"""
        return self.query_rows(
            keyword=keyword,
            columns=columns,
            match_mode=match_mode,
            case_sensitive=case_sensitive,
            limit=limit,
            sort_by=sort_by,
            ascending=ascending,
        )

    @staticmethod
    def _condition_mask(s: pd.Series, op: str, value, case_sensitive: bool) -> pd.Series:
        if op in ("isna", "is_null"):
            return s.isna()
        if op in ("notna", "not_null"):
            return s.notna()

        if op in ("gt", "gte", "lt", "lte"):
            left = pd.to_numeric(s, errors="coerce")
            right = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
            if pd.isna(right):
                return pd.Series(False, index=s.index)
            if op == "gt":
                return left > right
            if op == "gte":
                return left >= right
            if op == "lt":
                return left < right
            return left <= right

        left = s.astype(str)
        right = str(value)
        if not case_sensitive:
            left = left.str.lower()
            right = right.lower()

        if op == "contains":
            return left.str.contains(right, na=False, regex=False)
        if op == "not_contains":
            return ~left.str.contains(right, na=False, regex=False)
        if op == "ne":
            return left != right
        return left == right

    @staticmethod
    def _keyword_mask(
        df: pd.DataFrame,
        keyword: str,
        columns: list[str],
        match_mode: str,
        case_sensitive: bool,
    ) -> pd.Series:
        mask = pd.Series(False, index=df.index)
        needle = keyword if case_sensitive else keyword.lower()
        for col in columns:
            values = df[col].astype(str)
            if not case_sensitive:
                values = values.str.lower()
            if match_mode == "exact":
                mask |= values.eq(needle)
            else:
                mask |= values.str.contains(needle, na=False, regex=False)
        return mask

    def pivot_table(
        self, index: str, columns: str, values: str, aggfunc: str = "mean",
    ) -> pd.DataFrame:
        return pd.pivot_table(
            self.df, index=index, columns=columns, values=values, aggfunc=aggfunc
        ).round(4)

    def top_correlations(self, column: str, top_n: int = 5) -> pd.DataFrame:
        if column not in self.df.select_dtypes(include=[np.number]).columns:
            raise KeyError(f"列 '{column}' 不是数值列")
        numeric_df = self.df.select_dtypes(include=[np.number])
        corrs = numeric_df.corrwith(numeric_df[column]).drop(index=column)
        corrs = corrs.sort_values(key=lambda x: x.abs(), ascending=False).head(top_n)
        return pd.DataFrame({"相关系数": corrs.round(4), "绝对值": corrs.abs().round(4)})
