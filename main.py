import os

import telebot
from telebot import types
from dotenv import load_dotenv
from random import choice
import requests, json
import content

from tools import json_validate

load_dotenv()
API_TOKEN = os.getenv('TOKEN')
bot = telebot.TeleBot(API_TOKEN, parse_mode=None)

class InMemory:
    def __init__(self, vict=[], study=[]):
        self.vict = vict
        self.study = study
    def refresh_vict(self):
        with open("variants.json", "r") as vf:
            self.vict = json.loads(vf.read())
    def refresh_study(self):
        with open("study.json", "r") as sf:
            self.study = json.loads(sf.read())

mem = InMemory()
mem.refresh_vict()
mem.refresh_study()


@bot.message_handler(commands=['start'])
def handle_start(message):
    text = message.text
    user_id = message.chat.id
    keyboard = types.ReplyKeyboardMarkup()
    keyboard.row("Стартуем!")
    bot.send_message(
        user_id, 
        content.start_message, 
        reply_markup=keyboard
    )

@bot.message_handler(commands=['sudo'])
def handle_start(message):
    user_id = message.chat.id
    bot.send_message(user_id, content.sudo_message)
    bot.register_next_step_handler(message, check_sudo)

def check_sudo(message):
    text = message.text
    user_id = message.chat.id
    if text != os.getenv("SUDO"):
        bot.send_message(user_id, content.return_message)
        return
    bot.send_message(user_id, content.wait_json)
    bot.register_next_step_handler(message, add_questions)

def add_questions(message):
    text = message.text
    user_id = message.chat.id
    if type(text) == str:
        bot.send_message(user_id, content.wait_json)
        return
    file_info = bot.get_file(message.document.file_id)
    json_file = requests.get('https://api.telegram.org/file/bot{0}/{1}'.format(API_TOKEN, file_info.file_path))
    json_content = json_file.content

    study, vict = json_validate.validate(json_content)
    
    if vict:
        json_validate.json_concat_vict(json_content)
        mem.refresh_vict()
        bot.send_message(user_id, content.done_message)
    elif study:
        json_validate.json_concat_study(json_content)
        mem.refresh_study()
        bot.send_message(user_id, content.done_message)
    else:
        bot.send_message(user_id, content.return_message)

@bot.message_handler(content_types=["text"])
def handle_message(message):
    text = message.text
    user_id = message.chat.id
    keyboard = types.ReplyKeyboardMarkup()
    
    if text == "Обучение":
        keyboard.row("Обучение", "Викторина")
        var = choice(mem.study)
        
        bot.send_message(
            user_id, 
            f'{var["content"]}\nСсылка: {var["url"]}', 
            reply_markup=keyboard
        )
    else:
        var = choice(mem.vict)
        for r in var["vars"]:
            keyboard.row(str(r))

        bot.send_message(
            user_id, 
            var["ask"], 
            reply_markup=keyboard
        )
        bot.register_next_step_handler(message, checker, var)

def checker(message, var):
    text = message.text
    user_id = message.chat.id
    keyboard = types.ReplyKeyboardMarkup()
    t = ""
    if text == str(var["vars"][var["ans"]-1]):
        t = content.rigth
    else:
        t = content.noRight.format(str(var["ans"]))
    keyboard.row("Обучение", "Викторина")
    bot.send_message(user_id, t, reply_markup=keyboard)


if __name__ == "__main__":
    print("Bot is starting..")
    bot.polling(none_stop=True)