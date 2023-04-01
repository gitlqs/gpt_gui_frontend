import wx
from gpt_gui_frontend.ui import ChatFrame
from gpt_gui_frontend.api import OpenAIChatbot
from gpt_gui_frontend.utils import ensure_chat_history_dir, check_api_key

if __name__ == '__main__':
    if check_api_key():
        ensure_chat_history_dir()
        ai = OpenAIChatbot()
        app = wx.App()
        frame = ChatFrame(None, title='Chatbot Window', ai=ai)
        frame.Show()
        app.MainLoop()