"""🎯 分组聚合 & 异常检测页面"""

from ui.page_common import setup_page, require_df
from ui.tab_advanced import render

setup_page()
df, _ = require_df()
render(df)
