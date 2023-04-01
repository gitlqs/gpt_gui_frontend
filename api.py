import openai
import string
from gpt_gui_frontend.utils import parse_text_file

class OpenAIChatbot:
    def __init__(self):
        with open('../credential.txt', 'r') as f:
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