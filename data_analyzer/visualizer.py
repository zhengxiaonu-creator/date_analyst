"""数据可视化模块 - 支持保存 PNG 和返回 matplotlib figure（给 Streamlit 用）。"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


def _setup_chinese_font():
    candidates = ["PingFang SC", "Heiti TC", "STHeiti", "Songti SC",
                  "Noto Sans CJK SC", "WenQuanYi Micro Hei", "Microsoft YaHei",
                  "SimHei", "Arial Unicode MS"]
    plt.rcParams["font.sans-serif"] = candidates
    plt.rcParams["axes.unicode_minus"] = False


# 先设置 seaborn 主题，再配置中文字体（顺序关键：sns.set_theme 会重置 rcParams）
sns.set_theme(style="whitegrid", palette="viridis")
_setup_chinese_font()


class DataVisualizer:
    """生成常见的分析图表。支持：
      - 保存 PNG 文件（save_* 方法）
      - 直接返回 matplotlib figure（fig_* 方法，给 Streamlit 用）
    """

    def __init__(self, df: pd.DataFrame, output_dir: str = "outputs"):
        self.df = df
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.generated_files: list[str] = []

    # ---------- 内部工具 ----------
    def _save_fig(self, fig, filename: str) -> str:
        path = self.output_dir / filename
        fig.tight_layout()
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        self.generated_files.append(str(path))
        return str(path)

    # ---------- 直方图 ----------
    def fig_histogram(self, column: str, bins: int = 30) -> plt.Figure:
        if column not in self.df.select_dtypes(include=[np.number]).columns:
            raise KeyError(f"列 '{column}' 不是数值列")
        fig, ax = plt.subplots(figsize=(9, 5))
        sns.histplot(data=self.df, x=column, bins=bins, kde=True, ax=ax, color="#4C78A8")
        ax.set_title(f"{column} — 分布直方图", fontsize=14)
        ax.set_xlabel(column)
        ax.set_ylabel("频数")
        return fig

    def histogram(self, column: str, bins: int = 30) -> str:
        return self._save_fig(self.fig_histogram(column, bins), f"histogram_{column}.png")

    # ---------- 箱线图 ----------
    def fig_boxplot(self, column: str, group_by: Optional[str] = None) -> plt.Figure:
        if column not in self.df.select_dtypes(include=[np.number]).columns:
            raise KeyError(f"列 '{column}' 不是数值列")
        fig, ax = plt.subplots(figsize=(9, 5))
        if group_by:
            sns.boxplot(data=self.df, x=group_by, y=column, ax=ax, hue=group_by,
                        palette="Set2", legend=False)
            ax.set_title(f"{column} 按 {group_by} 分组的箱线图", fontsize=14)
            plt.xticks(rotation=30)
        else:
            sns.boxplot(data=self.df, y=column, ax=ax, color="#F58518")
            ax.set_title(f"{column} — 箱线图", fontsize=14)
        return fig

    def boxplot(self, column: str, group_by: Optional[str] = None) -> str:
        return self._save_fig(self.fig_boxplot(column, group_by),
                              f"boxplot_{column}_by_{group_by or 'none'}.png")

    # ---------- 条形图 ----------
    def fig_barplot(self, column: str, top_n: int = 10) -> plt.Figure:
        counts = self.df[column].value_counts().head(top_n)
        fig, ax = plt.subplots(figsize=(max(9, int(top_n * 0.9)), 5))
        sns.barplot(x=counts.index, y=counts.values, ax=ax, hue=counts.index,
                    palette="viridis", legend=False)
        ax.set_title(f"{column} — Top{top_n} 频数", fontsize=14)
        ax.set_ylabel("计数")
        plt.xticks(rotation=30, ha="right")
        return fig

    def barplot(self, column: str, top_n: int = 10) -> str:
        return self._save_fig(self.fig_barplot(column, top_n), f"barplot_{column}.png")

    # ---------- 热力图 ----------
    def fig_heatmap(self) -> Optional[plt.Figure]:
        numeric_df = self.df.select_dtypes(include=[np.number])
        if numeric_df.shape[1] < 2:
            return None
        fig, ax = plt.subplots(figsize=(max(8, numeric_df.shape[1] * 0.9), 6))
        corr = numeric_df.corr().round(2)
        sns.heatmap(corr, annot=True, cmap="coolwarm", center=0,
                    square=True, linewidths=0.5, ax=ax, fmt=".2f")
        ax.set_title("数值列相关性热力图", fontsize=14)
        return fig

    def heatmap(self) -> Optional[str]:
        fig = self.fig_heatmap()
        if fig is None:
            return None
        return self._save_fig(fig, "correlation_heatmap.png")

    # ---------- 散点图 ----------
    def fig_scatter(self, x_col: str, y_col: str) -> plt.Figure:
        for c in (x_col, y_col):
            if c not in self.df.select_dtypes(include=[np.number]).columns:
                raise KeyError(f"列 '{c}' 不是数值列")
        fig, ax = plt.subplots(figsize=(9, 6))
        sns.scatterplot(data=self.df, x=x_col, y=y_col, ax=ax, alpha=0.7, color="#E45756")
        ax.set_title(f"{y_col} vs {x_col}", fontsize=14)
        return fig

    def scatter(self, x_col: str, y_col: str) -> str:
        return self._save_fig(self.fig_scatter(x_col, y_col),
                              f"scatter_{x_col}_vs_{y_col}.png")

    # ---------- 缺失值 ----------
    def fig_missing_map(self) -> plt.Figure:
        fig, ax = plt.subplots(figsize=(9, 5))
        missing_pct = (self.df.isna().mean() * 100).sort_values(ascending=False)
        missing_pct = missing_pct[missing_pct > 0]
        if len(missing_pct) == 0:
            ax.text(0.5, 0.5, "无缺失值 ✅", ha="center", va="center", fontsize=16)
            ax.set_axis_off()
            ax.set_title("缺失值分布", fontsize=14)
            return fig
        colors = sns.color_palette("Reds_r", n_colors=len(missing_pct))
        sns.barplot(x=missing_pct.index, y=missing_pct.values, ax=ax, hue=missing_pct.index,
                    palette=colors, legend=False)
        ax.set_title("各列缺失率 (%)", fontsize=14)
        ax.set_ylabel("缺失率 (%)")
        plt.xticks(rotation=30, ha="right")
        return fig

    def missing_map(self) -> str:
        return self._save_fig(self.fig_missing_map(), "missing_values.png")

    # ---------- 折线图（分组聚合均值）----------
    def fig_line_grouped(self, x_col: str, y_col: str) -> plt.Figure:
        """按 x_col 分组聚合 y_col 均值的折线图。"""
        if y_col not in self.df.select_dtypes(include=[np.number]).columns:
            raise KeyError(f"列 '{y_col}' 不是数值列")
        grouped = self.df.groupby(x_col)[y_col].mean().sort_values(ascending=False)
        fig, ax = plt.subplots(figsize=(max(9, int(len(grouped) * 0.6)), 5))
        grouped.plot(kind="line", ax=ax, marker="o", color="#4C78A8", linewidth=2)
        ax.set_title(f"按 {x_col} 分组的 {y_col} 均值", fontsize=14)
        ax.set_ylabel(f"{y_col}（均值）")
        plt.xticks(rotation=30, ha="right")
        return fig

    # ---------- 自动化多图 ----------
    def auto_report(self, top_numeric: int = 4, top_categorical: int = 3) -> list[str]:
        """自动生成一组基础图表。返回保存的文件路径列表。"""
        files: list[str] = []
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()[:top_numeric]
        cat_cols = [c for c in self.df.select_dtypes(exclude=[np.number]).columns
                    if self.df[c].nunique() <= 20][:top_categorical]

        for col in numeric_cols:
            try:
                files.append(self.histogram(col))
            except Exception as e:
                print(f"  ⚠️  跳过 histogram({col}): {e}")
        for col in cat_cols:
            try:
                files.append(self.barplot(col))
            except Exception as e:
                print(f"  ⚠️  跳过 barplot({col}): {e}")
        try:
            path = self.heatmap()
            if path:
                files.append(path)
        except Exception as e:
            print(f"  ⚠️  跳过 heatmap: {e}")
        try:
            files.append(self.missing_map())
        except Exception as e:
            print(f"  ⚠️  跳过 missing_map: {e}")
        return files

    # ---------- 给 Streamlit 用的 figure 列表 ----------
    def auto_report_figures(
        self, top_numeric: int = 4, top_categorical: int = 3
    ) -> list[Tuple[str, plt.Figure]]:
        """返回 (标题, figure) 列表，直接给 Streamlit st.pyplot 用。"""
        figures: list[Tuple[str, plt.Figure]] = []
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()[:top_numeric]
        cat_cols = [c for c in self.df.select_dtypes(exclude=[np.number]).columns
                    if self.df[c].nunique() <= 20][:top_categorical]

        for col in numeric_cols:
            try:
                figures.append((f"📉 {col} — 分布直方图", self.fig_histogram(col)))
            except Exception:
                continue
        for col in cat_cols:
            try:
                figures.append((f"📊 {col} — 频数条形图", self.fig_barplot(col)))
            except Exception:
                continue
        try:
            fig = self.fig_heatmap()
            if fig is not None:
                figures.append(("🔥 数值列相关性热力图", fig))
        except Exception:
            pass
        try:
            figures.append(("❓ 缺失值分布", self.fig_missing_map()))
        except Exception:
            pass
        return figures
