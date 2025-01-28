import telebot
from telebot import types
import json
import time
from keep_alive import keep_alive
keep_alive()

# Botning tokeni va adminlar ro'yxati
TOKEN = '7812172716:AAGwWxaACbky4UDe_ivEQsOM0AqGviSnajo'
bot = telebot.TeleBot(TOKEN)
OWNER_ID = 7577190183

# Adminlar ro'yxatini yuklash funksiyasi
def load_admins():
    with open('admin.json', 'r') as admin_file:
        return json.load(admin_file)['admins']
    
def load_types():
    with open('types.json', 'r') as types_file:
        return json.load(types_file)['types']

admins = load_admins()

# Main menu funksiyasi
def main_menu(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton('🔖 Reklama')
    button2 = types.KeyboardButton('💰 Donat')
    button3 = types.KeyboardButton('👥 Admin')
    button4 = types.KeyboardButton('👤 Azolik')
    button5 = types.KeyboardButton('🔍 Akkaunt Izlash')
    markup.add(button1, button2)
    markup.add(button3, button4)
    markup.add(button5)
    
    if user_id == OWNER_ID or user_id in admins:
        button6 = types.KeyboardButton('⚙️ Setting')
        markup.add(button6)
        
    return markup

import json

# Foydalanuvchi ma'lumotlarini yuklash funksiyasi
def user_load():
    try:
        with open('user.json', 'r', encoding='utf-8') as user_file:
            return json.load(user_file)
    except FileNotFoundError:
        return {"users": []}

# Foydalanuvchi ma'lumotlarini yangilash funksiyasi
def user_save(users_data):
    with open('user.json', 'w', encoding='utf-8') as user_file:
        json.dump(users_data, user_file, ensure_ascii=False, indent=4)

@bot.message_handler(commands=['start'])
def start(message):
    if message.chat.type == 'private':
        users_data = user_load()
        if message.from_user.id not in users_data["users"]:
            users_data["users"].append(message.from_user.id)
            user_save(users_data)
        
        bot.send_message(message.chat.id, 'Xush kelibsiz!', reply_markup=main_menu(message.from_user.id))
    else:
        bot.send_message(message.chat.id, 'Akkaunt qidiruv uchun botga o\'ting.')

# Adminlar ro'yxatini har 60 soniyada qayta yuklash
def reload_admins_periodically():
    global admins
    while True:
        try:
            admins = load_admins()
        except Exception as e:
            error_message = f'Adminlar ro\'yxatini qayta yuklashda xatolik: {e}'
            bot.send_message(OWNER_ID, error_message)
        time.sleep(60)

import threading
threading.Thread(target=reload_admins_periodically).start()

@bot.message_handler(func=lambda message: message.text == '🔍 Akkaunt Izlash')
def search_account(message):
    types_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    def load_types():
        with open('types.json', 'r') as types_file:
            return json.load(types_file)['types']

    try:
        types_list = load_types()

        buttons = [types.KeyboardButton(type_item) for type_item in types_list]
        for i in range(0, len(buttons), 2):
            if i + 1 < len(buttons):
                types_markup.row(buttons[i], buttons[i + 1])
            else:
                types_markup.row(buttons[i])

        back_button = types.KeyboardButton('🔙 Orqaga')
        types_markup.add(back_button)

        bot.send_message(message.chat.id, 'Iltimos, bir tur tanlang:', reply_markup=types_markup)
    except Exception as e:
        bot.send_message(OWNER_ID, f'Xatolik yuz berdi: {e}')
        bot.send_message(message.chat.id, 'Xatolik yuz berdi. Keyinroq yana urinib ko\'ring.')

@bot.message_handler(func=lambda message: message.text in json.load(open('types.json', 'r'))['types'])
def handle_account_type_selection(message):
    selected_type = message.text
    try:
        bot.send_message(message.chat.id, f'Siz {selected_type} turini tanladingiz. Iltimos, byudjetingizni kiriting (faqat raqamlar):')
        bot.register_next_step_handler(message, ask_budget, selected_type)
    except Exception as e:
        bot.send_message(OWNER_ID, f'Xatolik yuz berdi: {e}')
        bot.send_message(message.chat.id, 'Xatolik yuz berdi. Keyinroq yana urinib ko\'ring.')

def ask_budget(message, selected_type):
    if not message.text or not message.text.isdigit():
        bot.send_message(message.chat.id, 'Iltimos, faqat raqamlar kiriting:', reply_markup=types.ForceReply())
        bot.register_next_step_handler(message, ask_budget, selected_type)
    else:
        try:
            budget = int(message.text)
            send_matching_accounts(message, selected_type, budget)
        except Exception as e:
            bot.send_message(OWNER_ID, f'Xatolik yuz berdi: {e}')
            bot.send_message(message.chat.id, 'Xatolik yuz berdi. Keyinroq yana urinib ko\'ring.')

def send_matching_accounts(message, selected_type, budget):
    try:
        with open('acc.json', 'r') as acc_file:
            accounts = json.load(acc_file)['Account']

        matching_accounts = [acc for acc in accounts if acc['type'] == selected_type and acc['cost'] <= budget]

        if not matching_accounts:
            bot.send_message(message.chat.id, f'{selected_type} turidan byudjetingizga mos keladigan akkaunt topilmadi.')
        else:
            for account in matching_accounts:
                try:
                    link_parts = account['link'].split('/')
                    channel_username = f"@{link_parts[-2]}"
                    message_id = int(link_parts[-1])
                    bot.copy_message(chat_id=message.chat.id, from_chat_id=channel_username, message_id=message_id, disable_notification=True)
                except Exception as e:
                    bot.send_message(OWNER_ID, f'Xabarni forward qilishda xatolik: {e}')

        bot.send_message(message.chat.id, 'Bosh menyu', reply_markup=main_menu(message.from_user.id))
    except Exception as e:
        bot.send_message(OWNER_ID, f'Xatolik yuz berdi: {e}')
        bot.send_message(message.chat.id, 'Xatolik yuz berdi. Keyinroq yana urinib ko\'ring.')

@bot.message_handler(func=lambda message: message.text == '💰 Donat')
def donate_handler(message):
    types_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    def load_types():
        with open('types.json', 'r') as types_file:
            return json.load(types_file)['types']

    try:
        types_list = load_types()

        buttons = []
        for idx, type_item in enumerate(types_list, start=1):
            button_text = f"{idx} {type_item}"
            buttons.append(types.KeyboardButton(button_text))

        for i in range(0, len(buttons), 2):
            if i + 1 < len(buttons):
                types_markup.row(buttons[i], buttons[i + 1])
            else:
                types_markup.row(buttons[i])

        back_button = types.KeyboardButton('🔙 Orqaga')
        types_markup.add(back_button)

        bot.send_message(message.chat.id, 'Iltimos, bir tur tanlang:', reply_markup=types_markup)
        
    except Exception as e:
        bot.send_message(OWNER_ID, f'Xatolik yuz berdi: {e}')
        bot.send_message(message.chat.id, 'Xatolik yuz berdi. Keyinroq yana urinib ko\'ring.')

@bot.message_handler(func=lambda message: message.text.split(' ')[0].isdigit())
def handle_donate_type_selection(message):
    try:
        selected_text = message.text.strip()
        selected_type = ' '.join(selected_text.split(' ')[1:])  # Raqamni olib tashlab, typeni oladi
        txt_filename = f"{selected_type}.txt"
        with open(txt_filename, 'r', encoding='utf-8') as txt_file:
            donate_message = txt_file.read()

        bot.send_message(message.chat.id, donate_message)
        bot.send_message(message.chat.id, 'Bosh menyu', reply_markup=main_menu(message.from_user.id))
    
    except Exception as e:
        bot.send_message(OWNER_ID, f'Xatolik yuz berdi: {e}')
        bot.send_message(message.chat.id, 'Xatolik yuz berdi. Keyinroq yana urinib ko\'ring.')


@bot.message_handler(func=lambda message: message.text == '🔖 Reklama')
def reklam_handler(message):
    try:
        bot.send_message(message.chat.id, '📣 Reklama uchun: @Std_admin bilan bog\'laning 📩')
    except Exception as e:
        bot.send_message(OWNER_ID, f'Xatolik yuz berdi: {e}')
        bot.send_message(message.chat.id, 'Xatolik yuz berdi. Keyinroq yana urinib ko\'ring.')

@bot.message_handler(func=lambda message: message.text == '👥 Admin')
def reklam_handler(message):
    try:
        bot.send_message(message.chat.id, '👥 Asosiy admin: @Std_admin bilan bog\'laning 📩')
    except Exception as e:
        bot.send_message(OWNER_ID, f'Xatolik yuz berdi: {e}')
        bot.send_message(message.chat.id, 'Xatolik yuz berdi. Keyinroq yana urinib ko\'ring.')

@bot.message_handler(func=lambda message: message.text == '👤 Azolik')
def join_handler(message):
    try:
        with open('join_message.txt', 'r', encoding='utf-8') as join_file:
            join_message = join_file.read()
        
        bot.send_message(message.chat.id, join_message, parse_mode='MarkdownV2')
    except Exception as e:
        bot.send_message(OWNER_ID, f'Xatolik yuz berdi: {e}')
        bot.send_message(message.chat.id, 'Xatolik yuz berdi. Keyinroq yana urinib ko\'ring.')


@bot.message_handler(func=lambda message: message.text == '⚙️ Setting')
def settings_handler(message):
    settings_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    # Tugmalarni qo'shish
    admins_button = types.KeyboardButton('🔹 Admins')
    json_button = types.KeyboardButton('📂 Jsonlar')
    txt_button = types.KeyboardButton('📄 Txtlar')
    add_acc_button = types.KeyboardButton('➕ Akk qo\'shish')
    remove_acc_button = types.KeyboardButton('➖ Akk ayrish')
    ad = types.KeyboardButton('📨 Reklama')
    back_button = types.KeyboardButton('🔙 Orqaga')

    settings_markup.add(admins_button)
    settings_markup.row(json_button, txt_button)
    settings_markup.row(add_acc_button, remove_acc_button)
    settings_markup.row(ad)
    settings_markup.add(back_button)

    bot.send_message(message.chat.id, '⚙️ Sozlamalar:', reply_markup=settings_markup)


@bot.message_handler(func=lambda message: message.text == '📨 Reklama' and message.from_user.id == OWNER_ID)
def reklama_handler(message):
    bot.send_message(message.chat.id, 'Iltimos, reklama xabarini yuboring (rasm, video, matn, gif, stik va hokazo):', reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, forward_reklama_to_users)

def forward_reklama_to_users(message):
    users_data = user_load()
    for user_id in users_data["users"]:
        try:
            bot.forward_message(user_id, message.chat.id, message.message_id)
        except Exception as e:
            print(f"Xatolik yuz berdi: {e}")
    
    bot.send_message(message.chat.id, 'Reklama xabari muvaffaqiyatli forward qilindi!', reply_markup=main_menu(message.from_user.id))

import random

@bot.message_handler(func=lambda message: message.text == '➕ Akk qo\'shish')
def add_account_handler(message):
    hide_markup = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, 'Iltimos, linkni yuboring:', reply_markup=hide_markup)
    bot.register_next_step_handler(message, ask_for_link)

def ask_for_link(message):
    link = message.text
    bot.send_message(message.chat.id, 'Iltimos, narxini yuboring (faqat raqamlar):')
    bot.register_next_step_handler(message, ask_for_cost, link)

def ask_for_cost(message, link):
    if not message.text.isdigit():
        bot.send_message(message.chat.id, 'Iltimos, faqat raqamlar kiriting:')
        bot.register_next_step_handler(message, ask_for_cost, link)
    else:
        cost = int(message.text)
        types_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        
        def load_types():
            with open('types.json', 'r') as types_file:
                return json.load(types_file)['types']
        
        types_list = load_types()
        
        buttons = [types.KeyboardButton(type_item) for type_item in types_list]
        for i in range(0, len(buttons), 2):
            if i + 1 < len(buttons):
                types_markup.row(buttons[i], buttons[i + 1])
            else:
                types_markup.row(buttons[i])
        
        new_type_button = types.KeyboardButton('Yangi type')
        types_markup.add(new_type_button)
        
        bot.send_message(message.chat.id, 'Iltimos, turini tanlang:', reply_markup=types_markup)
        bot.register_next_step_handler(message, ask_for_type, link, cost)

def ask_for_type(message, link, cost):
    selected_type = message.text
    if selected_type == 'Yangi type':
        bot.send_message(message.chat.id, 'Iltimos, yangi type kiriting:')
        bot.register_next_step_handler(message, ask_for_new_type, link, cost)
    else:
        generate_and_save_account(message, link, cost, selected_type)

def ask_for_new_type(message, link, cost):
    new_type = message.text
    with open('types.json', 'r', encoding='utf-8') as types_file:
        types_data = json.load(types_file)
    
    if new_type not in types_data['types']:
        types_data['types'].append(new_type)
        with open('types.json', 'w', encoding='utf-8') as types_file:
            json.dump(types_data, types_file, ensure_ascii=False, indent=4)
    
    generate_and_save_account(message, link, cost, new_type)

def generate_and_save_account(message, link, cost, selected_type):
    with open('acc.json', 'r', encoding='utf-8') as acc_file:
        accounts_data = json.load(acc_file)

    def generate_unique_id():
        while True:
            account_id = random.randint(10000, 99999)
            if not any(acc['id'] == account_id for acc in accounts_data['Account']):
                return account_id
    
    account_id = generate_unique_id()

    new_account = {
        "link": link,
        "cost": cost,
        "type": selected_type,
        "id": account_id
    }
    accounts_data['Account'].append(new_account)
    
    with open('acc.json', 'w', encoding='utf-8') as acc_file:
        json.dump(accounts_data, acc_file, ensure_ascii=False, indent=4)
    
    bot.send_message(message.chat.id, f"Yangi akkaunt muvaffaqiyatli qo'shildi! Uning ID si: {account_id}", reply_markup=main_menu(message.from_user.id))



@bot.message_handler(func=lambda message: message.text == '➖ Akk ayrish')
def remove_account_handler(message):
    hide_markup = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, 'Iltimos, ID raqamini yuboring:', reply_markup=hide_markup)
    bot.register_next_step_handler(message, ask_for_id_to_remove)

def ask_for_id_to_remove(message):
    try:
        account_id = int(message.text)
        with open('acc.json', 'r', encoding='utf-8') as acc_file:
            accounts_data = json.load(acc_file)
        
        account_exists = any(acc['id'] == account_id for acc in accounts_data['Account'])
        
        if account_exists:
            accounts_data['Account'] = [acc for acc in accounts_data['Account'] if acc['id'] != account_id]
            with open('acc.json', 'w', encoding='utf-8') as acc_file:
                json.dump(accounts_data, acc_file, ensure_ascii=False, indent=4)
            
            bot.send_message(message.chat.id, f"Akkaunt muvaffaqiyatli o'chirildi: ID {account_id}", reply_markup=main_menu(message.from_user.id))
        else:
            bot.send_message(message.chat.id, 'Bunday ID mavjud emas. Iltimos, qayta kiriting:')
            bot.register_next_step_handler(message, ask_for_id_to_remove)
    except ValueError:
        bot.send_message(message.chat.id, 'Iltimos, to\'g\'ri ID raqamini kiriting:')
        bot.register_next_step_handler(message, ask_for_id_to_remove)
    except Exception as e:
        bot.send_message(OWNER_ID, f'Xatolik yuz berdi: {e}')
        bot.send_message(message.chat.id, 'Xatolik yuz berdi. Keyinroq yana urinib ko\'ring.')

@bot.message_handler(func=lambda message: message.text == '🔹 Admins' and message.from_user.id == get_owner_id())
def admins_settings_handler(message):
    admin_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    add_admin_button = types.KeyboardButton('➕ Admin qo\'shish')
    remove_admin_button = types.KeyboardButton('➖ Admin ayrish')
    back_button = types.KeyboardButton('🔙 Orqaga')

    admin_markup.add(add_admin_button, remove_admin_button)
    admin_markup.add(back_button)

    bot.send_message(message.chat.id, 'Admin sozlamalari:', reply_markup=admin_markup)

def get_owner_id():
    with open('admin.json', 'r', encoding='utf-8') as admin_file:
        return json.load(admin_file)['owner_id']

@bot.message_handler(func=lambda message: message.text == '➕ Admin qo\'shish' and message.from_user.id == get_owner_id())
def add_admin_handler(message):
    hide_markup = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, 'Iltimos, qo\'shmoqchi bo\'lgan adminning 10 xonali ID raqamini kiriting:', reply_markup=hide_markup)
    bot.register_next_step_handler(message, ask_for_admin_id_to_add)

def ask_for_admin_id_to_add(message):
    try:
        admin_id = int(message.text)
        if len(message.text) != 10:
            raise ValueError("ID raqami 10 xonali bo'lishi kerak.")
        
        with open('admin.json', 'r', encoding='utf-8') as admin_file:
            admin_data = json.load(admin_file)
        
        if any(admin['id'] == admin_id for admin in admin_data['admins']):
            bot.send_message(message.chat.id, 'Bu ID allaqachon mavjud. Iltimos, boshqa ID kiriting:')
            bot.register_next_step_handler(message, ask_for_admin_id_to_add)
        else:
            admin_data['admins'].append({"id": admin_id, "name": f"Admin {len(admin_data['admins'])+1}"})
            with open('admin.json', 'w', encoding='utf-8') as admin_file:
                json.dump(admin_data, admin_file, ensure_ascii=False, indent=4)
            
            bot.send_message(message.chat.id, f"Yangi admin muvaffaqiyatli qo'shildi: ID {admin_id}", reply_markup=main_menu(message.from_user.id))
    except ValueError:
        bot.send_message(message.chat.id, 'Iltimos, to\'g\'ri 10 xonali ID raqamini kiriting:')
        bot.register_next_step_handler(message, ask_for_admin_id_to_add)
    except Exception as e:
        bot.send_message(OWNER_ID, f'Xatolik yuz berdi: {e}')
        bot.send_message(message.chat.id, 'Xatolik yuz berdi. Keyinroq yana urinib ko\'ring.')

@bot.message_handler(func=lambda message: message.text == '➖ Admin ayrish' and message.from_user.id == get_owner_id())
def remove_admin_handler(message):
    hide_markup = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, 'Iltimos, ayrilmoqchi bo\'lgan adminning 10 xonali ID raqamini kiriting:', reply_markup=hide_markup)
    bot.register_next_step_handler(message, ask_for_admin_id_to_remove)

def ask_for_admin_id_to_remove(message):
    try:
        admin_id = int(message.text)
        with open('admin.json', 'r', encoding='utf-8') as admin_file:
            admin_data = json.load(admin_file)
        
        if any(admin['id'] == admin_id for admin in admin_data['admins']):
            admin_data['admins'] = [admin for admin in admin_data['admins'] if admin['id'] != admin_id]
            with open('admin.json', 'w', encoding='utf-8') as admin_file:
                json.dump(admin_data, admin_file, ensure_ascii=False, indent=4)
            
            bot.send_message(message.chat.id, f"Admin muvaffaqiyatli ayrildi: ID {admin_id}", reply_markup=main_menu(message.from_user.id))
        else:
            bot.send_message(message.chat.id, 'Bunday ID mavjud emas. Iltimos, qayta kiriting:')
            bot.register_next_step_handler(message, ask_for_admin_id_to_remove)
    except ValueError:
        bot.send_message(message.chat.id, 'Iltimos, to\'g\'ri 10 xonali ID raqamini kiriting:')
        bot.register_next_step_handler(message, ask_for_admin_id_to_remove)
    except Exception as e:
        bot.send_message(OWNER_ID, f'Xatolik yuz berdi: {e}')
        bot.send_message(message.chat.id, 'Xatolik yuz berdi. Keyinroq yana urinib ko\'ring.')


import os

@bot.message_handler(func=lambda message: message.text == '📄 Txtlar' and message.from_user.id in [get_owner_id()] + [admin['id'] for admin in get_admins()])
def txt_files_handler(message):
    txt_files_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    txt_files = [f for f in os.listdir() if f.endswith('.txt')]
    
    buttons = [types.KeyboardButton(txt_file) for txt_file in txt_files]
    for i in range(0, len(buttons), 2):
        if i + 1 < len(buttons):
            txt_files_markup.row(buttons[i], buttons[i + 1])
        else:
            txt_files_markup.row(buttons[i])
    
    add_button = types.KeyboardButton('➕ Yangi txt qo\'shish')
    delete_button = types.KeyboardButton('❌ Delete txt')
    back_button = types.KeyboardButton('🔙 Orqaga')
    txt_files_markup.add(add_button, delete_button)
    txt_files_markup.add(back_button)
    
    bot.send_message(message.chat.id, 'Iltimos, bir .txt fayl tanlang yoki yangi .txt fayl qo\'shing:', reply_markup=txt_files_markup)

def get_admins():
    with open('admin.json', 'r', encoding='utf-8') as admin_file:
        return json.load(admin_file)['admins']

def get_owner_id():
    with open('admin.json', 'r', encoding='utf-8') as admin_file:
        return json.load(admin_file)['owner_id']

@bot.message_handler(func=lambda message: message.text in [f for f in os.listdir() if f.endswith('.txt')])
def handle_existing_txt_selection(message):
    selected_txt = message.text
    bot.send_message(message.chat.id, f'Iltimos, yangi matnni kiriting ({selected_txt} fayli uchun):', reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, update_txt_file, selected_txt)

def update_txt_file(message, selected_txt):
    new_text = message.text
    with open(selected_txt, 'w', encoding='utf-8') as txt_file:
        txt_file.write(new_text)
    bot.send_message(message.chat.id, f'{selected_txt} muvaffaqiyatli yangilandi!', reply_markup=main_menu(message.from_user.id))

@bot.message_handler(func=lambda message: message.text == '➕ Yangi txt qo\'shish')
def add_new_txt_handler(message):
    bot.send_message(message.chat.id, 'Iltimos, yangi .txt fayl nomini kiriting:', reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, ask_for_new_txt_name)

def ask_for_new_txt_name(message):
    new_txt_name = message.text
    if not new_txt_name.endswith('.txt'):
        new_txt_name += '.txt'
    bot.send_message(message.chat.id, f'Iltimos, {new_txt_name} fayli uchun matnni kiriting:')
    bot.register_next_step_handler(message, create_new_txt_file, new_txt_name)

def create_new_txt_file(message, new_txt_name):
    new_text = message.text
    with open(new_txt_name, 'w', encoding='utf-8') as txt_file:
        txt_file.write(new_text)
    bot.send_message(message.chat.id, f'Yangi {new_txt_name} fayli muvaffaqiyatli yaratildi!', reply_markup=main_menu(message.from_user.id))

@bot.message_handler(func=lambda message: message.text == '❌ Delete txt')
def delete_txt_handler(message):
    txt_files_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    txt_files = [f for f in os.listdir() if f.endswith('.txt')]
    
    buttons = [types.KeyboardButton(f"{idx+1} {txt_file}") for idx, txt_file in enumerate(txt_files)]
    for i in range(0, len(buttons), 2):
        if i + 1 < len(buttons):
            txt_files_markup.row(buttons[i], buttons[i + 1])
        else:
            txt_files_markup.row(buttons[i])
    
    back_button = types.KeyboardButton('🔙 Orqaga')
    txt_files_markup.add(back_button)
    
    bot.send_message(message.chat.id, 'Iltimos, o\'chirmoqchi bo\'lgan .txt faylni tanlang:', reply_markup=txt_files_markup)
    bot.register_next_step_handler(message, confirm_delete_txt)

def confirm_delete_txt(message):
    selected_text = message.text.strip()
    txt_index = int(selected_text.split()[0]) - 1
    selected_txt = selected_text.split(" ", 1)[1]
    
    if selected_txt.endswith('.txt'):
        os.remove(selected_txt)
        bot.send_message(message.chat.id, f'{selected_txt} fayli muvaffaqiyatli o\'chirildi!', reply_markup=main_menu(message.from_user.id))
    else:
        bot.send_message(message.chat.id, 'Tanlangan fayl topilmadi. Qayta urinib ko\'ring.', reply_markup=main_menu(message.from_user.id))

import os

@bot.message_handler(func=lambda message: message.text == '📂 Jsonlar' and message.from_user.id == get_owner_id())
def json_files_handler(message):
    json_files_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    json_files = [f for f in os.listdir() if f.endswith('.json')]
    
    buttons = [types.KeyboardButton(json_file) for json_file in json_files]
    for i in range(0, len(buttons), 2):
        if i + 1 < len(buttons):
            json_files_markup.row(buttons[i], buttons[i + 1])
        else:
            json_files_markup.row(buttons[i])
    
    add_button = types.KeyboardButton('➕ Yangi json qo\'shish')
    delete_button = types.KeyboardButton('❌ Delete json')
    back_button = types.KeyboardButton('🔙 Orqaga')
    json_files_markup.add(add_button, delete_button)
    json_files_markup.add(back_button)
    
    bot.send_message(message.chat.id, 'Iltimos, bir .json fayl tanlang yoki yangi .json fayl qo\'shing:', reply_markup=json_files_markup)

def get_owner_id():
    with open('admin.json', 'r', encoding='utf-8') as admin_file:
        return json.load(admin_file)['owner_id']

@bot.message_handler(func=lambda message: message.text in [f for f in os.listdir() if f.endswith('.json')])
def handle_existing_json_selection(message):
    selected_json = message.text
    bot.send_message(message.chat.id, f'Iltimos, yangi matnni kiriting ({selected_json} fayli uchun):', reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, update_json_file, selected_json)

def update_json_file(message, selected_json):
    new_text = message.text
    with open(selected_json, 'w', encoding='utf-8') as json_file:
        json_file.write(new_text)
    bot.send_message(message.chat.id, f'{selected_json} muvaffaqiyatli yangilandi!', reply_markup=main_menu(message.from_user.id))

@bot.message_handler(func=lambda message: message.text == '➕ Yangi json qo\'shish')
def add_new_json_handler(message):
    bot.send_message(message.chat.id, 'Iltimos, yangi .json fayl nomini kiriting:', reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, ask_for_new_json_name)

def ask_for_new_json_name(message):
    new_json_name = message.text
    if not new_json_name.endswith('.json'):
        new_json_name += '.json'
    bot.send_message(message.chat.id, f'Iltimos, {new_json_name} fayli uchun matnni kiriting:')
    bot.register_next_step_handler(message, create_new_json_file, new_json_name)

def create_new_json_file(message, new_json_name):
    new_text = message.text
    with open(new_json_name, 'w', encoding='utf-8') as json_file:
        json_file.write(new_text)
    bot.send_message(message.chat.id, f'Yangi {new_json_name} fayli muvaffaqiyatli yaratildi!', reply_markup=main_menu(message.from_user.id))

@bot.message_handler(func=lambda message: message.text == '❌ Delete json')
def delete_json_handler(message):
    json_files_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    json_files = [f for f in os.listdir() if f.endswith('.json')]
    
    buttons = [types.KeyboardButton(f"{idx+1} {json_file}") for idx, json_file in enumerate(json_files)]
    for i in range(0, len(buttons), 2):
        if i + 1 < len(buttons):
            json_files_markup.row(buttons[i], buttons[i + 1])
        else:
            json_files_markup.row(buttons[i])
    
    back_button = types.KeyboardButton('🔙 Orqaga')
    json_files_markup.add(back_button)
    
    bot.send_message(message.chat.id, 'Iltimos, o\'chirmoqchi bo\'lgan .json faylni tanlang:', reply_markup=json_files_markup)
    bot.register_next_step_handler(message, confirm_delete_json)

def confirm_delete_json(message):
    selected_text = message.text.strip()
    json_index = int(selected_text.split()[0]) - 1
    selected_json = selected_text.split(" ", 1)[1]
    
    if selected_json.endswith('.json'):
        os.remove(selected_json)
        bot.send_message(message.chat.id, f'{selected_json} fayli muvaffaqiyatli o\'chirildi!', reply_markup=main_menu(message.from_user.id))
    else:
        bot.send_message(message.chat.id, 'Tanlangan fayl topilmadi. Qayta urinib ko\'ring.', reply_markup=main_menu(message.from_user.id))


@bot.message_handler(func=lambda message: message.text == '🔙 Orqaga')
def go_back(message):
    try:
        bot.send_message(message.chat.id, 'Bosh menyu', reply_markup=main_menu(message.from_user.id))
    except Exception as e:
        bot.send_message(OWNER_ID, f'Xatolik yuz berdi: {e}')
        bot.send_message(message.chat.id, 'Xatolik yuz berdi. Keyinroq yana urinib ko\'ring.')

bot.polling(none_stop=True)
