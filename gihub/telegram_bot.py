import telebot
import logging
import json
import threading
from dotenv import load_dotenv
import os
from pyTrader import GoldTrader  # Importojmë strategjinë

# Inicioni logging për të parë mesazhet në terminal
logging.basicConfig(level=logging.INFO)

# Ngarko variablat e ambientit nga skedari .env
load_dotenv()
API_TOKEN = os.getenv('TELEGRAM_API_TOKEN')
bot = telebot.TeleBot(API_TOKEN)

# Variabël global për të mbajtur gjendjen e përdoruesve dhe strategjisë
user_data = {}
bot_running = {}
strategy_params = {}

# Ngarko të dhënat e përdoruesve nga skedari JSON
def load_user_data():
    try:
        with open('user_data.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Ruaj të dhënat e përditësuara të përdoruesve në skedarin JSON
def save_user_data():
    with open('user_data.json', 'w') as f:
        json.dump(user_data, f, indent=4)
# Ngarko parametrat e strategjisë nga skedari JSON
def load_strategy_params():
    try:
        with open('strategy_params.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "SYMBOL": "XAUUSD",
            "TIMEFRAME": "TIMEFRAME_M5",
            "EMA_PERIOD": 12,
            "TP_PERCENT": 0.0045,
            "SL_PERCENT": 0.01
        }

# Ruaj parametrat e strategjisë në skedarin JSON
def save_strategy_params():
    with open('strategy_params.json', 'w') as f:
        json.dump(strategy_params, f, indent=4)

# Funksioni për të rifilluar bot-in për përdoruesit që kanë qenë aktivë më parë
def resume_bot_for_active_users():
    for chat_id, data in user_data.items():
        if data.get('active', False):  # Kontrollo nëse ishte aktiv para se kodi të ndalej
            bot.send_message(chat_id, "Rifillimi automatik i bot-it, bazuar në parametrat tuaj të ruajtur.")
            threading.Thread(target=run_strategy, args=(chat_id,)).start()

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = str(message.chat.id)
    
    if chat_id not in user_data:
        bot.send_message(chat_id, "Për të filluar, ju lutemi përdorni /login për të futur të dhënat tuaja.")
    else:
        bot.send_message(chat_id, "Mirë se vini! Ju mund të përdorni komandat për të modifikuar strategjinë tuaj.")
        if user_data[chat_id].get('active', False):
            bot.send_message(chat_id, "Strategjia juaj është duke u ekzekutuar. Përdorni /stop_bot për të ndaluar atë.")
        else:
            bot.send_message(chat_id, "Ju mund të përdorni /start_bot për të filluar strategjinë.")

# /login për të marrë të dhënat e përdoruesit
@bot.message_handler(commands=['login'])
def login(message):
    chat_id = str(message.chat.id)
    bot.send_message(chat_id, "Ju lutemi shkruani emrin tuaj të përdoruesit MT5:")
    bot.register_next_step_handler(message, get_username)

def get_username(message):
    chat_id = str(message.chat.id)
    username = message.text
    if chat_id not in user_data:
        user_data[chat_id] = {}
    user_data[chat_id]['username'] = username
    bot.send_message(chat_id, "Ju lutemi shkruani fjalëkalimin tuaj MT5:")
    bot.register_next_step_handler(message, get_password)

def get_password(message):
    chat_id = str(message.chat.id)
    password = message.text
    user_data[chat_id]['password'] = password
    bot.send_message(chat_id, "Ju lutemi shkruani serverin tuaj MT5:")
    bot.register_next_step_handler(message, get_server)

def get_server(message):
    chat_id = str(message.chat.id)
    server = message.text
    user_data[chat_id]['server'] = server
    save_user_data()
    bot.send_message(chat_id, "Detajet e hyrjes janë ruajtur! Tani mund të përdorni /start_bot për të filluar tregtimin.")

# Komanda për të treguar opsionet e rregullimeve
@bot.message_handler(commands=['rregullime'])
def rregullime(message):
    chat_id = str(message.chat.id)
    bot.send_message(chat_id, f"Ti je perdoruesi *{chat_id}*\nCfar deshironi te ndrryshoni?\n"
                              "/SYMBOL  -> XAUUSD\n"
                              "/TIMEFRAME -> TIMEFRAME_M5\n"
                              "/EMA_PERIOD -> 12\n"
                              "/TP_PERCENT -> 0.0045\n"
                              "/SL_PERCENT -> 0.01")

# Funksionet për secilin parametër
@bot.message_handler(commands=['SYMBOL'])
def change_symbol(message):
    chat_id = str(message.chat.id)
    bot.send_message(chat_id, "Ju lutemi fusni SYMBOL e ri:")
    bot.register_next_step_handler(message, set_symbol)

def set_symbol(message):
    chat_id = str(message.chat.id)
    strategy_params['SYMBOL'] = message.text.strip()
    save_strategy_params()
    bot.send_message(chat_id, f"SYMBOL u përditësua në {strategy_params['SYMBOL']}")

@bot.message_handler(commands=['TIMEFRAME'])
def change_timeframe(message):
    chat_id = str(message.chat.id)
    bot.send_message(chat_id, "Ju lutemi fusni TIMEFRAME e ri (psh. TIMEFRAME_M5):")
    bot.register_next_step_handler(message, set_timeframe)

def set_timeframe(message):
    chat_id = str(message.chat.id)
    strategy_params['TIMEFRAME'] = message.text.strip()
    save_strategy_params()
    bot.send_message(chat_id, f"TIMEFRAME u përditësua në {strategy_params['TIMEFRAME']}")

@bot.message_handler(commands=['EMA_PERIOD'])
def change_ema_period(message):
    chat_id = str(message.chat.id)
    bot.send_message(chat_id, "Ju lutemi fusni EMA_PERIOD e ri:")
    bot.register_next_step_handler(message, set_ema_period)

def set_ema_period(message):
    chat_id = str(message.chat.id)
    try:
        strategy_params['EMA_PERIOD'] = int(message.text.strip())
        save_strategy_params()
        bot.send_message(chat_id, f"EMA_PERIOD u përditësua në {strategy_params['EMA_PERIOD']}")
    except ValueError:
        bot.send_message(chat_id, "Ju lutemi fusni një numër valid për EMA_PERIOD.")

@bot.message_handler(commands=['TP_PERCENT'])
def change_tp_percent(message):
    chat_id = str(message.chat.id)
    bot.send_message(chat_id, "Ju lutemi fusni TP_PERCENT e ri (psh. 0.0045):")
    bot.register_next_step_handler(message, set_tp_percent)

def set_tp_percent(message):
    chat_id = str(message.chat.id)
    try:
        strategy_params['TP_PERCENT'] = float(message.text.strip())
        save_strategy_params()
        bot.send_message(chat_id, f"TP_PERCENT u përditësua në {strategy_params['TP_PERCENT']}")
    except ValueError:
        bot.send_message(chat_id, "Ju lutemi fusni një numër valid për TP_PERCENT.")

@bot.message_handler(commands=['SL_PERCENT'])
def change_SL_PERCENT(message):
    chat_id = str(message.chat.id)
    bot.send_message(chat_id, "Ju lutemi fusni SL_PERCENT të ri (psh. 0.01):")
    bot.register_next_step_handler(message, set_SL_PERCENT)

def set_SL_PERCENT(message):
    chat_id = str(message.chat.id)
    try:
        strategy_params['SL_PERCENT'] = float(message.text.strip())
        save_strategy_params()
        bot.send_message(chat_id, f"SL_PERCENT u përditësua në {strategy_params['SL_PERCENT']}")
    except ValueError:
        bot.send_message(chat_id, "Ju lutemi fusni një numër valid për SL_PERCENT.")

    
# Komanda për të nisur strategjinë
@bot.message_handler(commands=['start_bot'])
def start_bot(message):
    chat_id = str(message.chat.id)
    if chat_id in user_data:
        bot.send_message(chat_id, "Duke nisur robotin me parametrat e dhënë...")
        user_data[chat_id]['active'] = True  # Vendos që përdoruesi është aktiv
        save_user_data()  # Ruaj gjendjen e re
        threading.Thread(target=run_strategy, args=(chat_id,)).start()
    else:
        bot.send_message(chat_id, "Ju lutemi vendosni parametrat duke përdorur komandën /rregullime")

# Funksioni që nis strategjinë në një thread më vete
def run_strategy(chat_id):
    params = user_data.get(chat_id)
    
    if params:
        # Kalo bot-in dhe chat_id si argumente për dërgimin e mesazheve te përdoruesi
        trader = GoldTrader(params, bot=bot, chat_id=chat_id)
        trader.main()
    else:
        bot.send_message(chat_id, "Nuk ka parametra të vendosur. Përdorni /rregullime për t'i vendosur.")

# Komanda për të ndalur strategjinë
@bot.message_handler(commands=['stop_bot'])
def stop_bot(message):
    chat_id = str(message.chat.id)
    bot.send_message(chat_id, "Ndalimi i botit...")
    user_data[chat_id]['active'] = False  # Vendos që përdoruesi është joaktiv
    save_user_data()  # Ruaj gjendjen e re
    bot.send_message(chat_id, "Bot është ndalur. Per te rifilluar perseri shtypni /start_bot")

# Komanda për të parë statusin e botit
@bot.message_handler(commands=['status'])
def get_status(message):
    chat_id = str(message.chat.id)
    if user_data.get(chat_id, {}).get('active', False):
        trader = GoldTrader()
        ema, current_close = trader.get_ema()
        bot.send_message(chat_id, f"EMA aktual: {ema}\nMbyllja aktuale: {current_close}")
    else:
        bot.send_message(chat_id, "Boti nuk është duke u ekzekutuar. Përdorni /start_bot për të filluar.")

# Ngarko të dhënat e përdoruesve kur boti starton dhe rifillo bot-et aktive
if __name__ == '__main__':
    user_data = load_user_data()
    strategy_params = load_strategy_params()
    resume_bot_for_active_users()  # Rifillo botin për përdoruesit që kanë qenë aktivë
    bot.polling(none_stop=True)
