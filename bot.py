from telebot.types import InlineKeyboardMarkup as Markup
from telebot.types import InlineKeyboardButton as Button
from time import sleep
import telebot
import sqlite3 
import json

with open('settings.json', 'r') as f:
    data = json.load(f)

bot = telebot.TeleBot(token = data['TOKEN'])

def database():
    conn = sqlite3.connect('base.db')
    cur = conn.cursor()
    return conn, cur

def shopper(message, id_item):
    conn, cur = database()
    cur.execute("SELECT item_name FROM item_shop WHERE item_id = (?)", (id_item,))
    name = cur.fetchone()[0]
    cur.execute("SELECT item_path FROM item_shop WHERE item_id = (?)", (id_item,))
    path = cur.fetchone()[0]
    cur.execute("SELECT item_price FROM item_shop WHERE item_id = (?)", (id_item,))
    price = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM item_shop")
    rows = cur.fetchone()[0]
    buttons = Markup(row_width = 3)
    #[back, score, forward, buy]
    back = Button(text = '<-', callback_data='back')
    score = Button(text = f'{id_item}/{rows}', callback_data='none')
    forward = Button(text = '->', callback_data='forward')
    buy = Button(text = 'buy', callback_data='buy')
    main_back = Button(text = 'меню', callback_data='menu')
    buttons.add(back, score, forward, buy)
    item_photo = open(path, 'rb')
    shop_message = bot.send_photo(message.chat.id, photo=item_photo, caption= f'{name}, price: {price}$', reply_markup = buttons)
    return shop_message

def starter(message):
    number = 1
    conn, cur = database()
    id_user = message.chat.id
    cur.execute('SELECT id_user FROM user_table WHERE id_user = (?)', (id_user,))
    user = cur.fetchone()
    if user == None:
        cur.execute('INSERT INTO user_table (id_user) VALUES (?)', (id_user,))
        conn.commit()
    buttons = Markup(row_width=2)
    first_name = message.from_user.first_name
    shop = Button(text = 'магазин', callback_data='shop')
    balance = Button(text = 'баланс', callback_data='balance')
    plus_balance = Button(text = 'Добавить\n500$', callback_data='plus_balance')
    basket = Button(text = 'Список покупок', callback_data = 'basket')
    buttons.add(shop, balance, plus_balance, basket)
    bot.send_message(message.chat.id, text = f'Привет {first_name}! Добро пожаловать в наш магазин! 🛍️  Здесь вы найдете лего', reply_markup=buttons)


def listed(a):
    var = []
    for x in a:
        var.append(x)
    return var

@bot.message_handler(commands=['start'])
def index(message):
    global number
    number = 1
    starter(message)

@bot.callback_query_handler(func=lambda callback: True)
def butt(call):
    global number
    conn, cur = database()
    message = None
    data = call.data
    user_id = call.message.chat.id
    s = ''
    if data == 'shop':
        message = shopper(call.message, number)
    elif data == 'forward':
        cur.execute("SELECT COUNT(*) FROM item_shop")
        rows = cur.fetchone()[0]
        if number < rows:
            number += 1
            message = shopper(call.message, number)
        
    elif data == 'back':
        if number > 1:
            number -= 1
            message = shopper(call.message, number)
    elif data == 'plus_balance':
        cur.execute("SELECT balance FROM user_table WHERE id_user = (?)", (user_id,))
        balance = cur.fetchone()[0]
        balance = int(balance) + 500
        cur.execute("UPDATE user_table SET balance = (?) WHERE id_user = (?)", (balance, user_id))
        conn.commit()
        plus = bot.send_message(call.message.chat.id, text = 'Добавлено 500$')
        sleep(1)
        bot.delete_message(call.message.chat.id, plus.id)
    elif data == 'balance':
        cur.execute("SELECT balance FROM user_table WHERE id_user = (?)", (user_id,))
        balance = cur.fetchone()[0]
        button = Markup()
        further = Button(text = 'далее', callback_data='menu')
        button.add(further)
        bot.send_message(call.message.chat.id, text = f'Баланс: {balance}$', reply_markup = button)
    elif data == 'menu':
        starter(call.message)
    elif data == 'buy':
        buttons = Markup(row_width = 2)
        yes = Button(text = 'Да!', callback_data='yes')
        menu = Button(text = 'В меню', callback_data='menu')
        buttons.add(yes, menu)
        bot.send_message(call.message.chat.id, text = 'Вы уверены что хотите купить данный товар?', reply_markup=buttons)
    elif data == 'yes':
        buttons = Markup()
        menu = Button(text = 'В меню', callback_data='menu')
        buttons.add(menu)
        cur.execute("SELECT item_price FROM item_shop WHERE item_id = (?)", (number,))
        price = cur.fetchone()[0]
        cur.execute("SELECT balance FROM user_table WHERE id_user = (?)", (user_id,))
        balance = cur.fetchone()[0]
        if balance > price:
            balance -= price
            cur.execute('UPDATE user_table SET balance = (?) WHERE id_user = (?)', (balance, user_id))
            conn.commit()
            cur.execute('SELECT buy_list FROM user_table WHERE id_user = (?)', (user_id,))
            buy_list = str(cur.fetchone()[0])
            if buy_list != "None":
                buy_list += f'{number} '
                cur.execute("UPDATE user_table SET buy_list = (?) WHERE id_user = (?)", (buy_list, user_id))
            else:
                s += f'{number} '
                cur.execute("UPDATE user_table SET buy_list = (?) WHERE id_user = (?)", (s, user_id))
            
            conn.commit()
            cur.execute("SELECT item_name FROM item_shop WHERE item_id = (?)", (number,))
            name = cur.fetchone()[0]
            bot.send_message(call.message.chat.id, text = f'Товар  "{name}", успешно куплен', reply_markup=buttons)
        else:
            bot.send_message(call.message.chat.id, text = 'У вас не хватает денег', reply_markup=buttons)
    elif data == 'basket':
        cur.execute('SELECT buy_list FROM user_table WHERE id_user = (?)', (user_id,))
        l_buy = str(cur.fetchone()[0])
        if l_buy != "None":
            list_buy = listed(l_buy)
            listed_buy = ''
            for x in list_buy:
                cur.execute("SELECT item_name FROM item_shop WHERE item_id = (?)", (int(x),))
                listed_buy += f'{cur.fetchone()[0]}\n'
            bot.send_message(call.message.chat.id, text = f'Ваш список покупок:\n{listed_buy}')
        else:
            bot.send_message(call.message.chat.id, text = 'Ваш список покупок пуст')
        
    try:
        if data in ['forward', 'back']:
            bot.delete_message(call.message.chat.id, call.message.id)
    except AttributeError as e:
        print(f"Error deleting message: {e}")


bot.infinity_polling()