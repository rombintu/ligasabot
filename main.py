import os, sys, time
import telebot

from telebot import types
from dotenv import load_dotenv
from random import choice

import requests, json
import content

from pymongo import MongoClient
from tools import json_validate

load_dotenv()

API_TOKEN = os.getenv('TOKEN')
CONNECTION_STRING = os.getenv("CONNECTION_STRING")

if API_TOKEN == None or CONNECTION_STRING == None:
    print("env vars TOKEN or CONNECTION_STRING is None")
    sys.exit(1)

bot = telebot.TeleBot(API_TOKEN, parse_mode=None)

class Database:
    db = MongoClient(CONNECTION_STRING)[content.userdb]
    def login_check(self, user_id):
        return self.db.table.find_one({"user_id": str(user_id)})

    def sign_up(self, message):
        keyboard = types.ReplyKeyboardMarkup()
        keyboard.row(choice(content.starts_buttons))
        try:
            self.db.table.insert_one({
                    "user_id": str(message.chat.id),
                    "nick": str(message.text),
                    "faileds": [],
                    "rights": [],
                }
            )
            bot.reply_to(message, content.reg_ok, reply_markup=keyboard)
        except:
            bot.reply_to(message, content.database_problems)

    def update(self, user_id, failed, field="failed"):
        self.db.table.update_one(
            {"user_id": str(user_id)},
            {"$push": {
                field: failed
                }, 
            }, upsert=False)

class InMemory:
    # modes = content.modes
    modes = [f"day{i}" for i in range(1, 13)]

    # Нужна для обработки ошибок
    cur_mode = modes[0]
    db = MongoClient(CONNECTION_STRING)[cur_mode]
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
        self.db = MongoClient(CONNECTION_STRING)[self.cur_mode]

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

# GLOBAL START
mem = InMemory()
mem.refresh()

users = Database()
# GLOBAL END

@bot.message_handler(commands=['start'])
def handle_message_start(message):
    keyboard = types.ReplyKeyboardMarkup()
    # keyboard.row(choice(content.starts_buttons))
    bot.send_message(
        message.chat.id, 
        content.start_message, 
        reply_markup=keyboard
    )

@bot.message_handler(commands=['sudo'])
def handle_message_sudo(message):
    bot.send_message(message.chat.id, content.sudo_message)
    bot.register_next_step_handler(message, sudo_add_content)

@bot.message_handler(commands=['help'])
def handle_message_sudo(message):
    keyboard = types.ReplyKeyboardMarkup()
    keyboard.row(choice(content.starts_buttons))
    bot.send_message(message.chat.id, content.help_message, reply_markup=keyboard)

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

@bot.message_handler(commands=['edu'])
def handle_message(message):
    user_id = message.chat.id
    keyboard = types.ReplyKeyboardMarkup()
    if len(mem.study) == 0:
        keyboard.row(content.get_rand_vict)
        bot.send_message(user_id, content.database_study_is_empty.format(mem.cur_mode))
        return
    try:
        for v in mem.study:
            keyboard.row(str(v["title"]))
    except:
        pass
    bot.send_message(user_id, content.select_themes, reply_markup=keyboard)

@bot.message_handler(content_types=["text"])
def handle_message(message):
    text = message.text
    user_id = message.chat.id
    user_info = users.login_check(user_id)
    if not user_info:
        keyboard = types.ReplyKeyboardRemove()
        for msg in content.not_reg:
            bot.send_message(user_id, msg, reply_markup=keyboard)
            time.sleep(1)
        bot.register_next_step_handler(message, users.sign_up)
        return

    rights = user_info["rights"]
    vict = None
    keyboard = types.ReplyKeyboardMarkup()
    

    for st in mem.study:
        try:
            if text == st["title"]:
                keyboard.row("Получить рандомный вопрос")
                bot.send_message(
                    user_id, 
                    f'{st["content"]}\nСсылка: {st["url"]}', 
                    reply_markup=keyboard
                )
                return
        except Exception as e:
            bot.send_message(
                    user_id, 
                    f'Error: {str(e)}\nПингани администратора'
                )
    else:
        try:
            keys = []
            for v in mem.vict:
                keys.append(v["ask"])

            vict_key = choice(list(set(keys) - set(rights))) # Убираем вопросы на которые уже ответили

            for v in mem.vict: # TODO
                if v["ask"] == vict_key:
                    vict = v

        except IndexError:
            bot.send_message(user_id, content.database_is_empty.format(mem.cur_mode))
            return
        
        if not vict:
            bot.send_message(user_id, content.database_is_empty.format(mem.cur_mode))
            return

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
        t = choice(content.rigth)
        users.update(user_id, var["ask"], field="rights")
    else:
        t = choice(content.noRight) + "\nПравильный ответ: " + (str(var["vars"][var["ans"]-1]))
        users.update(user_id, var["ask"], field="faileds")

    keyboard.row("Получить рандомный вопрос")
    bot.send_message(user_id, t, reply_markup=keyboard)

def main():
    print("Bot is starting..")
    bot.polling(none_stop=True, timeout=60)

if __name__ == "__main__":
    main()