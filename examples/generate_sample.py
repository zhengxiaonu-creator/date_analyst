"""生成示例数据脚本。运行: python examples/generate_sample.py"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def main():
    rng = np.random.default_rng(42)
    categories = ["电子产品", "服装", "食品", "图书", "家居"]
    regions = ["华北", "华东", "华南", "华西", "东北"]
    genders = ["男", "女"]
    n = 500

    df = pd.DataFrame({
        "ID": range(1, n + 1),
        "类别": rng.choice(categories, n),
        "地区": rng.choice(regions, n),
        "性别": rng.choice(genders, n),
        "年龄": rng.integers(18, 65, n),
        "销售额": np.round(rng.exponential(500, n), 2),
        "数量": rng.integers(1, 10, n),
        "评分": np.round(rng.uniform(1.0, 5.0, n), 2),
    })
    df.loc[rng.choice(n, 25, replace=False), "评分"] = np.nan
    df.loc[rng.choice(n, 10, replace=False), "销售额"] = np.nan
    df.loc[rng.choice(n, 5, replace=False), "销售额"] *= 10

    out_path = Path(__file__).parent / "sample_data.csv"
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"✅ 已生成: {out_path} ({len(df)} 行 × {len(df.columns)} 列)")


if __name__ == "__main__":
    main()
