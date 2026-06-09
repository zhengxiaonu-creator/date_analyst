"""数据加载模块 - 支持 CSV 和 Excel 文件（含 Streamlit 上传文件）。"""

from __future__ import annotations

import os
from io import BytesIO
from pathlib import Path
from typing import Optional, Union

import pandas as pd


PathLike = Union[str, os.PathLike, Path]


class DataLoader:
    """加载 CSV / Excel 文件为 pandas DataFrame。"""

    SUPPORTED_EXTS = {".csv", ".xlsx", ".xls"}

    def __init__(self, default_encoding: str = "utf-8"):
        self.default_encoding = default_encoding

    def load(
        self,
        file_path: Optional[PathLike] = None,
        file_object=None,
        file_name: Optional[str] = None,
        sheet_name: Optional[Union[str, int]] = 0,
        encoding: Optional[str] = None,
        **kwargs,
    ) -> pd.DataFrame:
        """根据文件扩展名自动选择加载方式。

        支持两种输入：
          - file_path: 本地文件路径
          - file_object + file_name: 用于 Streamlit 的上传文件对象
        """
        if file_object is not None:
            name = file_name or (getattr(file_object, "name", "data") or "data")
            ext = Path(name).suffix.lower()
            if ext == ".csv":
                return self._load_csv_from_fileobj(file_object, encoding=encoding, **kwargs)
            if ext in (".xlsx", ".xls"):
                return pd.read_excel(file_object, sheet_name=sheet_name, **kwargs)
            raise ValueError(f"不支持的文件格式: {ext}。支持: .csv, .xlsx, .xls")

        if file_path is None:
            raise ValueError("必须提供 file_path 或 file_object")

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {path}")

        ext = path.suffix.lower()
        if ext not in self.SUPPORTED_EXTS:
            raise ValueError(
                f"不支持的文件格式: {ext}。支持: {sorted(self.SUPPORTED_EXTS)}"
            )

        if ext == ".csv":
            return self._load_csv(path, encoding=encoding, **kwargs)
        return self._load_excel(path, sheet_name=sheet_name, **kwargs)

    def _load_csv(
        self,
        path: Path,
        encoding: Optional[str] = None,
        **kwargs,
    ) -> pd.DataFrame:
        encodings_to_try = [encoding, self.default_encoding, "utf-8-sig", "gbk", "latin-1"]
        encodings_to_try = [e for e in encodings_to_try if e]
        for enc in encodings_to_try:
            try:
                return pd.read_csv(path, encoding=enc, **kwargs)
            except UnicodeDecodeError:
                continue
            except Exception:
                if enc == encodings_to_try[-1]:
                    raise
                continue
        raise UnicodeDecodeError("utf-8", b"", 0, 1, f"无法用常见编码解析 CSV: {path}")

    def _load_csv_from_fileobj(
        self,
        file_object,
        encoding: Optional[str] = None,
        **kwargs,
    ) -> pd.DataFrame:
        encodings_to_try = [encoding, self.default_encoding, "utf-8-sig", "gbk", "latin-1"]
        encodings_to_try = [e for e in encodings_to_try if e]
        raw_data = file_object.read()
        if isinstance(raw_data, str):
            raw_data = raw_data.encode("utf-8")
        for enc in encodings_to_try:
            try:
                return pd.read_csv(BytesIO(raw_data), encoding=enc, **kwargs)
            except UnicodeDecodeError:
                continue
            except Exception:
                if enc == encodings_to_try[-1]:
                    raise
                continue
        raise UnicodeDecodeError("utf-8", b"", 0, 1, "无法用常见编码解析 CSV 文件")

    def _load_excel(
        self,
        path: Path,
        sheet_name: Optional[Union[str, int]] = 0,
        **kwargs,
    ) -> pd.DataFrame:
        return pd.read_excel(path, sheet_name=sheet_name, **kwargs)

    def list_sheets(self, file_path: Optional[PathLike] = None, file_object=None) -> list[str]:
        """列出 Excel 文件中的所有 sheet 名称。"""
        if file_object is not None:
            return pd.ExcelFile(file_object).sheet_names
        if file_path is None:
            raise ValueError("必须提供 file_path 或 file_object")
        path = Path(file_path)
        if path.suffix.lower() not in (".xlsx", ".xls"):
            raise ValueError("只有 Excel 文件支持 sheet 列表")
        return pd.ExcelFile(path).sheet_names


def load_data(
    file_path: Optional[PathLike] = None,
    sheet_name: Optional[Union[str, int]] = 0,
    **kwargs,
) -> pd.DataFrame:
    """便捷函数：加载数据。"""
    return DataLoader().load(file_path=file_path, sheet_name=sheet_name, **kwargs)
