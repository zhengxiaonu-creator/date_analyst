"""🖼️ 可视化图表页面"""

from ui.page_common import setup_page, require_df
from ui.tab_visualization import render

setup_page()
df, _ = require_df()
render(df)
