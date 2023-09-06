import os, sys, time
import telebot

from telebot import types
from dotenv import load_dotenv
from random import choice

# import requests, json
import content

from pymongo import MongoClient
from tools import utils

load_dotenv()

API_TOKEN = os.getenv('TOKEN')
CONNECTION_STRING = os.getenv("CONNECTION_STRING")
Markdown = "MarkdownV2"
if API_TOKEN == None:
    print("TOKEN is None")
    sys.exit(1)

bot = telebot.TeleBot(API_TOKEN, parse_mode=None)

class Database:
    db = MongoClient(CONNECTION_STRING)[content.userdb]
    def login_check(self, user_id):
        return self.db.table_new.find_one({"user_id": str(user_id)})

    def sign_up(self, message):
        keyboard = types.ReplyKeyboardMarkup()
        for btn in content.starts_buttons:
            keyboard.row(btn)
        try:
            self.db.table_new.insert_one({
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
        self.db.table_new.update_one(
            {"user_id": str(user_id)},
            {"$push": {
                field: failed
                }, 
            }, upsert=False)

google_sheet = utils.Google_Sheets(os.getcwd(), os.getenv("SPREADSHEET_ID"), os.getenv("RANGE"))
try:
    google_sheet.O2Auth()
except Exception as err:
    print(err)
    sys.exit(1)

class InMemory:
    # modes = content.modes
    modes = [f'{i}' for i in range(1, 13)]

    # Нужна для обработки ошибок
    cur_mode = utils.read_day(default=modes[0])
    # db = MongoClient(CONNECTION_STRING)[cur_mode]
    vict = []
    # study = []

    def refresh(self):
        self.vict = []
        vict, errors = google_sheet.parse_data_by_day(self.cur_mode)
        if errors:
            return errors
        self.vict = vict
        return None

    def change_mode(self, mode):
        self.cur_mode = mode
        utils.write_day(mode)

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
        reply_markup=keyboard,
        parse_mode=Markdown
    )

@bot.message_handler(commands=['help'])
def handle_message_sudo(message):
    keyboard = types.ReplyKeyboardMarkup()
    keyboard.row(choice(content.starts_buttons))
    bot.send_message(message.chat.id, content.help_message, reply_markup=keyboard, parse_mode=Markdown)

@bot.message_handler(commands=['mode'])
def handle_message_mode(message):
    user_id = message.chat.id
    bot.send_message(user_id, content.sudo_message, parse_mode=Markdown)
    bot.register_next_step_handler(message, sudo_change_mode)

def sudo_change_mode(message):
    text = message.text
    user_id = message.chat.id
    if text != os.getenv("SUDO"):
        bot.send_message(user_id, content.return_message, parse_mode=Markdown)
        return
    keyboard = types.ReplyKeyboardMarkup()
    for m in mem.modes:
        keyboard.row(m)
    bot.send_message(user_id, content.change_mode, reply_markup=keyboard, parse_mode=Markdown)
    bot.register_next_step_handler(message, change_mode)

def change_mode(message):
    mem.change_mode(message.text)
    errors = mem.refresh()
    if not errors:
        bot.send_message(message.chat.id, content.done_message, reply_markup=types.ReplyKeyboardRemove())
    else:
        bot.send_message(message.chat.id, "Не удалось выполнить, тк есть ошибки\n" + "\n".join(errors), reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(content_types=["text"])
def handle_message(message):
    text = message.text
    user_id = message.chat.id
    user_info = users.login_check(user_id)
    if not user_info:
        keyboard = types.ReplyKeyboardRemove()
        for msg in content.not_reg:
            bot.send_message(user_id, msg, reply_markup=keyboard, parse_mode=Markdown)
            time.sleep(3)
        bot.register_next_step_handler(message, users.sign_up)
        return

    rights = user_info["rights"]
    vict = None
    keyboard = types.ReplyKeyboardMarkup()
    

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

    keyboard.row("[Интеллект] Ответить на следующий вопрос")
    bot.send_message(user_id, t, reply_markup=keyboard)

def main():
    print("Bot is starting..")
    bot.polling(none_stop=True, timeout=60)

if __name__ == "__main__":
    main()