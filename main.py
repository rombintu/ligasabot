import os

import telebot
from telebot import types
from dotenv import load_dotenv
from random import choice
import requests, json
import content
from pymongo import MongoClient
import pymongo

from tools import json_validate

load_dotenv()
API_TOKEN = os.getenv('TOKEN')
bot = telebot.TeleBot(API_TOKEN, parse_mode=None)

class InMemory:
    # Key - отображение имени в боте
    # Value - название базы данных
    modes = {"1 раздел":"bot", "2 раздел":"glava_2"}

    # Нужна для обработки ошибок
    cur_mode = list(modes.keys())[0]
    db = MongoClient(os.getenv("CONNECTION_STRING"))[modes[cur_mode]]
    vict = []
    study = []

    def refresh(self):
        self.vict = []
        self.study = []
        for el in self.db.vict.find():
            self.vict.append(el)
        for el in self.db.study.find():
            self.study.append(el)

    def change_mode(self, mode):
        self.cur_mode = mode
        self.db = MongoClient(os.getenv("CONNECTION_STRING"))[self.modes[self.cur_mode]]

    def concat_vict(self, json_content):
        content = json.loads(json_content.decode("utf-8"))
        if type(content) != list:
            content = [content]
        self.db.vict.insert_many(content)

    def concat_study(self, json_content):
        content = json.loads(json_content.decode("utf-8"))
        if type(content) != list:
            content = [content]
        self.db.study.insert_many(content)

mem = InMemory()
mem.refresh()


@bot.message_handler(commands=['start'])
def handle_message_start(message):
    text = message.text
    user_id = message.chat.id
    keyboard = types.ReplyKeyboardMarkup()
    keyboard.row(choice(content.starts_buttons))
    bot.send_message(
        user_id, 
        content.start_message, 
        reply_markup=keyboard
    )

@bot.message_handler(commands=['sudo'])
def handle_message_sudo(message):
    user_id = message.chat.id
    bot.send_message(user_id, content.sudo_message)
    bot.register_next_step_handler(message, sudo_add_content)

@bot.message_handler(commands=['mode'])
def handle_message_mode(message):
    user_id = message.chat.id
    bot.send_message(user_id, content.sudo_message)
    bot.register_next_step_handler(message, sudo_chage_mode)

def sudo_add_content(message):
    text = message.text
    user_id = message.chat.id
    if text != os.getenv("SUDO"):
        bot.send_message(user_id, content.return_message)
        return
    bot.send_message(user_id, content.wait_json)
    bot.register_next_step_handler(message, add_questions)

def sudo_chage_mode(message):
    text = message.text
    user_id = message.chat.id
    if text != os.getenv("SUDO"):
        bot.send_message(user_id, content.return_message)
        return
    keyboard = types.ReplyKeyboardMarkup()
    for m in mem.modes:
        keyboard.row(m)
    bot.send_message(user_id, content.change_mode, reply_markup=keyboard)
    bot.register_next_step_handler(message, change_mode)

def change_mode(message):
    mem.change_mode(message.text)
    mem.refresh()
    bot.send_message(message.chat.id, content.done_message, reply_markup=types.ReplyKeyboardRemove())

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
        mem.concat_vict(json_content)
        mem.refresh()
        bot.send_message(user_id, content.done_message)
    elif study:
        mem.concat_study(json_content)
        mem.refresh()
        bot.send_message(user_id, content.done_message)
    else:
        bot.send_message(user_id, content.return_message)

@bot.message_handler(content_types=["text"])
def handle_message(message):
    text = message.text
    user_id = message.chat.id
    keyboard = types.ReplyKeyboardMarkup()
    try:
        study = choice(mem.study)
        vict = choice(mem.vict)
    except IndexError:
        bot.send_message(user_id, content.database_is_empty.format(mem.cur_mode))
        return

    if text == "Обучение":
        keyboard.row("Обучение", "Викторина")
        bot.send_message(
            user_id, 
            f'{study["content"]}\nСсылка: {study["url"]}', 
            reply_markup=keyboard
        )
    else:
        for v in vict["vars"]:
            keyboard.row(str(v))
        bot.send_message(
            user_id, 
            vict["ask"], 
            reply_markup=keyboard
        )
        bot.register_next_step_handler(message, checker, vict)

def checker(message, var):
    text = message.text
    user_id = message.chat.id
    keyboard = types.ReplyKeyboardMarkup()
    t = ""
    if text == str(var["vars"][var["ans"]-1]):
        t = content.rigth
    else:
        t = content.noRight.format(str(var["vars"][var["ans"]-1]))
    keyboard.row("Обучение", "Викторина")
    bot.send_message(user_id, t, reply_markup=keyboard)

def main():
    print("Bot is starting..")
    bot.polling(none_stop=True, timeout=60)

if __name__ == "__main__":
    main()