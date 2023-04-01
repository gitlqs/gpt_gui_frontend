import time
import os

import wx
import wx.html2
import html
import markdown2

from gpt_gui_frontend.utils import append_chat_history, format_chat_history

css_style = """
    body {
        font-family: Arial, sans-serif;
        font-size: 14px;
        line-height: 1.4;
        margin: 0;
        padding: 10px;
        background-color: #f7f7f7;
    }

    .chat {
        margin: 10px;
        padding: 10px;
        border-radius: 5px;
    }

    .chat.user {
        background-color: #d7e3f2;
    }

    .chat.bot {
        background-color: #f2d7d7;
    }

    .chat .header {
        font-weight: bold;
        margin-bottom: 5px;
    }

    .chat .content {
        margin-top: 5px;
    }
"""


class ChatFrame(wx.Frame):
    def __init__(self, parent, title, ai):

        super(ChatFrame, self).__init__(parent, title=title, size=(800, 800))

        self.current_chat_history_file_name = None
        self.renamed = False
        self.ai = ai

        # create a panel
        panel = wx.Panel(self)

        # create a sizer to arrange the elements
        sizer = wx.BoxSizer(wx.VERTICAL)

        # create a splitter window to allow resizing of the workspace
        splitter = wx.SplitterWindow(panel, style=wx.SP_LIVE_UPDATE)
        splitter.SetMinimumPaneSize(100)

        # create a text control to show the chat history
        self.history_ctrl = wx.html2.WebView.New(splitter, backend=wx.html2.WebViewBackendEdge)

        # create a text control for the user input with increased font size
        font = wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.input_ctrl = wx.TextCtrl(splitter, style=wx.TE_MULTILINE)
        self.input_ctrl.SetFont(font)

        splitter.SplitHorizontally(self.history_ctrl, self.input_ctrl)
        splitter.SetSashPosition(int(self.GetSize().GetHeight() * 0.75))  # Set the initial position of the resize bar
        sizer.Add(splitter, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)

        # create a horizontal sizer for the chat input
        input_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # create a button to create a new chat
        new_chat_btn = wx.Button(panel, label='New Chat')
        input_sizer.Add(new_chat_btn, flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, border=5)

        # create a button to load chat history
        load_chat_btn = wx.Button(panel, label='Load')
        input_sizer.Add(load_chat_btn, flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, border=5)

        # create a button to send the user input
        send_btn = wx.Button(panel, label='Send')
        input_sizer.Add(send_btn, flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, border=5)

        # add the input sizer to the main sizer
        sizer.Add(input_sizer, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=5)

        # set the main sizer for the panel
        panel.SetSizer(sizer)

        # bind events for the buttons
        new_chat_btn.Bind(wx.EVT_BUTTON, self.on_new_chat)
        send_btn.Bind(wx.EVT_BUTTON, self.on_send)
        self.input_ctrl.Bind(wx.EVT_KEY_DOWN, self.on_input_key_down)
        load_chat_btn.Bind(wx.EVT_BUTTON, self.on_load_chat)

    def on_load_chat(self, event):
        # save the current zoom level
        current_zoom_level = self.history_ctrl.GetZoom()

        self.renamed = True
        dlg = wx.FileDialog(self, message="Choose a chat history file", wildcard="*.*", style=wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.current_chat_history_file_name = dlg.GetPath()
            with open(self.current_chat_history_file_name, 'r', encoding='utf-8') as f:
                chat_content = format_chat_history(f.read())
            # print(chat_content)
            self.history_ctrl.SetPage(chat_content, css_style)
        dlg.Destroy()

        # scroll to the bottom of the chat history
        self.history_ctrl.RunScript("window.scrollTo(0, document.body.scrollHeight);")
        # restore the previous zoom level
        self.history_ctrl.SetZoom(current_zoom_level)

    def on_new_chat(self, event):
        self.history_ctrl.SetPage('', '')
        self.renamed = False

    def on_send(self, event):
        user_input = self.input_ctrl.GetValue()

        # save the current zoom level
        current_zoom_level = self.history_ctrl.GetZoom()

        if user_input:
            # print(self.history_ctrl.GetPageSource())
            if self.history_ctrl.GetPageSource() == '<html><head></head><body></body></html>':
                self.current_chat_history_file_name = './chat_history/' + str(time.time()) + '.txt'

            append_chat_history(filename=self.current_chat_history_file_name,
                                chat='#$#user#$#\n' + user_input + '\n')


            # add user's chat to chat history
            page_source = self.history_ctrl.GetPageSource()
            page_source += '<div class="chat user"><div class="header">-------------------You-------------------<br><br></div><div class="content">{}<br></div></div>'.format(
                html.escape(user_input))
            self.history_ctrl.SetPage(page_source, css_style)

            # add bot's chat to chat history
            bot_content = self.ai.get_answer(filename=self.current_chat_history_file_name)
            bot_html = markdown2.markdown(bot_content, extras=['fenced-code-blocks'])
            bot_response = '<div class="chat bot"><div class="header">-------------------Bot-------------------</div><div class="content">{}</div></div>'.format(
                bot_html)
            page_source = self.history_ctrl.GetPageSource()
            page_source += bot_response
            self.history_ctrl.SetPage(page_source, css_style)
            append_chat_history(filename=self.current_chat_history_file_name,
                                chat='#$#assistant#$#\n' + bot_content + '\n')

            # clear user input control
            self.input_ctrl.Clear()

            # scroll to the bottom of the chat history
            self.history_ctrl.RunScript("window.scrollTo(0, document.body.scrollHeight);")
            # restore the previous zoom level
            self.history_ctrl.SetZoom(current_zoom_level)

            if not self.renamed:
                #print(f'{self.current_chat_history_file_name=}')
                #with open(self.current_chat_history_file_name, 'r', encoding='utf-8') as f:
                #    print(f.read())
                new_filename = self.ai.rename_chat_history(self.current_chat_history_file_name)
                #print(f'{new_filename=}')
                os.rename(self.current_chat_history_file_name, './chat_history/'+new_filename+'.txt')
                self.current_chat_history_file_name = './chat_history/' + new_filename +'.txt'
                self.renamed = True

    def on_input_key_down(self, event):
        key_code = event.GetKeyCode()
        modifiers = event.GetModifiers()

        if key_code == wx.WXK_RETURN and modifiers == wx.MOD_CONTROL:
            self.on_send(event)
        else:
            event.Skip()