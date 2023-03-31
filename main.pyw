#! .\\Scripts\\pythonw.exe

import wx
import random
import time
import wx.html2
import markdown2
import os
import html
import openai
import string

class openai_obj:
    def __init__(self):
        with open('credential.txt', 'r') as f:
            openai.api_key = f.read().strip()

    def get_answer(self, filename):
        completion = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            # stream=True,
            messages=parse_text_file(filename)
        )

        bot_content = completion.choices[0].message.content
        return bot_content

    def rename_chat_history(self, filename):
        messages = parse_text_file(filename)
        messages.append({'role': 'user',
                         'content': 'summarize the above conversation within 7 English words. do not include any punctuations so that I can use it as a file name. do not output any explanatory text. output the summary only.'})
        # print(f'{messages=}')
        completion = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=messages
        )

        new_filename = completion.choices[0].message.content
        return new_filename.translate(str.maketrans('', '', string.punctuation))


def parse_text_file(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    conversations = []
    current_conversation = {}
    for line in lines:
        if line.startswith('#$#'):
            if current_conversation:
                conversations.append(current_conversation)
            current_conversation = {'role': line.strip('#$#\n'), 'content': ''}
        else:
            current_conversation['content'] += line

    if current_conversation:
        conversations.append(current_conversation)

    return conversations


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
    def __init__(self, parent, title):

        super(ChatFrame, self).__init__(parent, title=title, size=(800, 800))

        self.current_chat_history_file_name = None
        self.renamed = False

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
        splitter.SetSashPosition(self.GetSize().GetHeight() * 0.75)  # Set the initial position of the resize bar
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
            bot_content = ai.get_answer(filename=self.current_chat_history_file_name)
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
                new_filename = ai.rename_chat_history(self.current_chat_history_file_name)
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


def append_chat_history(filename, chat):
    with open(filename, 'a', encoding='utf-8') as file:
        file.write(chat)


def format_chat_history(chat_history):
    # Split chat history into separate messages
    messages = chat_history.strip().split('#$#')

    # Create a list to store formatted chat messages
    formatted_messages = []

    # Loop through messages and format each one
    for i in range(1, len(messages), 2):
        if messages[i] == 'user':
            user_message = messages[i+1]
            formatted_messages.append(f'<div class="chat user"><div class="header">-------------------You-------------------<br><br></div><div class="content">{html.escape(user_message)}<br></div></div>')
        elif messages[i] == 'assistant':
            bot_message = messages[i+1]
            bot_message_html = markdown2.markdown(bot_message, extras=['fenced-code-blocks'])
            formatted_messages.append(f'<div class="chat bot"><div class="header">-------------------Bot-------------------</div><div class="content">{bot_message_html}</div></div>')

    # Join the formatted messages into a single string
    formatted_chat_history = ''.join(formatted_messages)

    # Wrap the formatted messages in an HTML document
    return '<html><head></head><body>{}</body></html>'.format(formatted_chat_history)

def check_api_key():
    api_key_file = 'credential.txt'
    flag = False
    # print(os.path.exists(api_key_file))
    if not os.path.exists(api_key_file):
        flag = False
        app = wx.App()
        dlg = wx.TextEntryDialog(None, 'Please enter your API key:', 'API Key Required')

        while True:
            if dlg.ShowModal() == wx.ID_OK:
                api_key = dlg.GetValue()
                if api_key.strip() != "" and api_key.startswith("sk-"):
                    with open(api_key_file, 'w') as file:
                        file.write(api_key)
                    dlg.Destroy()
                    flag = True
                    break
                else:
                    error_dlg = wx.MessageDialog(None, 'Invalid API key. Please enter a valid API key starting with "sk-".',
                                                 style=wx.OK)
                    error_dlg.ShowModal()
                    error_dlg.Destroy()
            else:
                dlg.Destroy()
                wx.Exit()
    else:
        flag = True

    return flag

if __name__ == '__main__':
    if check_api_key():
        ai = openai_obj()
        app = wx.App()
        frame = ChatFrame(None, title='Chatbot Window')
        frame.Show()
        app.MainLoop()
