"""💬 对话式 Agent 页面"""

from ui.page_common import setup_page, get_df
from ui.tab_chat_agent import render

setup_page()
df, file_name = get_df()
render(df, file_name)
