"""演示如何在 Python 脚本中调用 Agent 的 API。运行: python examples/example_usage.py"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data_analyzer.agent import DataAgent


def main():
    sample = Path(__file__).parent / "sample_data.csv"
    if not sample.exists():
        print(f"❌ 未找到 {sample}，请先运行 examples/generate_sample.py")
        sys.exit(1)

    # 方式1：对话式 Agent
    print("=" * 60)
    print("🤖 方式一：对话式 Agent.ask()")
    print("=" * 60)
    agent = DataAgent(output_dir="outputs")
    print(agent.load_file(str(sample)))
    print("\n问: 概览")
    print(agent.ask("概览")[:600] + "...")
    print("\n问: 查找 华东")
    print(agent.ask("查找 华东"))
    print("\n问: 找出 销售额 大于 1000 的行")
    print(agent.ask("找出 销售额 大于 1000 的行"))
    print("\n问: 按 类别 聚合 销售额")
    print(agent.ask("按 类别 聚合 销售额"))
    print("\n问: 相关性")
    print(agent.ask("相关性"))
    print("\n问: 画 年龄 直方图")
    print(agent.ask("画 年龄 直方图"))

    print("\n" + "=" * 60)
    print("✅ 完成。图表保存在 outputs/ 目录")


if __name__ == "__main__":
    main()
