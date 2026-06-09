"""命令行入口：python main.py 启动对话式 Agent。

用法:
    python main.py                          # 交互模式
    python main.py data.csv                 # 预先加载 data.csv 再交互
    python main.py data.csv -c "概览"       # 执行一次性命令
    python main.py data.csv -c "自动图表" -o ./outputs
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from data_analyzer.agent import AGENT_NAME, DataAgent


def main():
    parser = argparse.ArgumentParser(description=AGENT_NAME)
    parser.add_argument("file", nargs="?", default=None,
                        help="要分析的 CSV/Excel 文件路径（可选）")
    parser.add_argument("-c", "--command", help="执行一次性命令后退出")
    parser.add_argument("-o", "--output", default="outputs",
                        help="图表输出目录（默认 outputs/）")
    args = parser.parse_args()

    agent = DataAgent(output_dir=args.output)

    if args.file:
        msg = agent.load_file(file_path=args.file)
        print(msg)
        if msg.startswith("❌"):
            sys.exit(1)

    if args.command:
        reply = agent.ask(args.command)
        print(reply)
        return

    agent.chat()


if __name__ == "__main__":
    main()
