"""📈 统计分析页面"""

from ui.page_common import setup_page, require_df
from ui.tab_analysis import render

setup_page()
df, file_name = require_df()
render(df, file_name)
