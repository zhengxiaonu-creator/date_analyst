"""测试 DataLoader — 多编码回退、加载后校验。"""

import io
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data_analyzer.data_loader import DataLoader, load_data


class TestDataLoader:
    """DataLoader 核心功能测试。"""

    def test_load_empty_df_raises(self):
        """空 DataFrame 应抛出 ValueError。"""
        loader = DataLoader()
        with pytest.raises(ValueError, match="文件为空"):
            loader._validate_loaded_df(pd.DataFrame())

    def test_load_duplicate_columns_raises(self):
        """重复列名应抛出 ValueError。"""
        loader = DataLoader()
        df = pd.DataFrame({"a": [1], "b": [2]})
        df.columns = ["x", "x"]
        with pytest.raises(ValueError, match="存在重复列名"):
            loader._validate_loaded_df(df)

    def test_validate_loaded_df_ok(self):
        """正常 DataFrame 应通过校验。"""
        loader = DataLoader()
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        result = loader._validate_loaded_df(df)
        assert result is df

    def test_load_csv_utf8(self, tmp_path):
        """加载 UTF-8 编码的 CSV。"""
        csv_path = tmp_path / "test.csv"
        csv_path.write_text("姓名,年龄\n张三,25\n李四,30", encoding="utf-8")
        df = load_data(str(csv_path))
        assert len(df) == 2
        assert list(df.columns) == ["姓名", "年龄"]

    def test_load_csv_gbk(self, tmp_path):
        """加载 GBK 编码的 CSV（多编码回退）。"""
        csv_path = tmp_path / "test_gbk.csv"
        csv_path.write_text("姓名,年龄\n张三,25\n李四,30", encoding="gbk")
        df = load_data(str(csv_path))
        assert len(df) == 2
        assert list(df.columns) == ["姓名", "年龄"]

    def test_load_csv_from_fileobj(self):
        """从 BytesIO 加载 CSV。"""
        data = io.BytesIO("姓名,年龄\n张三,25\n李四,30".encode("utf-8"))
        loader = DataLoader()
        df = loader.load(file_object=data, file_name="test.csv")
        assert len(df) == 2

    def test_load_unsupported_format(self):
        """不支持的格式应抛出 ValueError。"""
        loader = DataLoader()
        with pytest.raises(ValueError, match="不支持的文件格式"):
            loader.load(file_object=io.BytesIO(b"x"), file_name="test.txt")

    def test_load_nonexistent_file(self):
        """不存在的文件应抛出 FileNotFoundError。"""
        with pytest.raises(FileNotFoundError):
            load_data("/nonexistent/file.csv")

    def test_supported_extensions(self):
        """确认支持的扩展名列表。"""
        assert ".csv" in DataLoader.SUPPORTED_EXTS
        assert ".xlsx" in DataLoader.SUPPORTED_EXTS
        assert ".xls" in DataLoader.SUPPORTED_EXTS

    def test_list_sheets_non_excel_raises(self, tmp_path):
        """非 Excel 文件调用 list_sheets 应抛出 ValueError。"""
        csv_path = tmp_path / "test.csv"
        csv_path.write_text("a,b\n1,2")
        loader = DataLoader()
        with pytest.raises(ValueError, match="只有 Excel 文件支持"):
            loader.list_sheets(file_path=str(csv_path))
