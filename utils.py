import html
import markdown2
import os


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
    api_key_file = '../credential.txt'
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


def ensure_chat_history_dir():
    chat_history_dir = './chat_history'
    if not os.path.exists(chat_history_dir):
        os.makedirs(chat_history_dir)