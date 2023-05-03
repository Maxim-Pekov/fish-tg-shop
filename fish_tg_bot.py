import logging
import redis
from environs import Env
from functools import partial
from main import fetch_products, fetch_access_token, fetch_product_by_id, fetch_product_photo_by_id, fetch_photo_by_id
from main import fetch_product_prices, fetch_prices_book, create_client, \
    fetch_product_stock, fetch_access_marker, get_branch, \
    put_product_to_branch, fetch_products_branch, remove_product_from_cart

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Filters, Updater
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler


env = Env()
env.read_env()

_database = None


def start(bot, update, access_token, client_id):

    products = fetch_products(access_token)
    keyboard = []
    for product in products['data']:
        keyboard.append([InlineKeyboardButton(product['attributes']['name'],
                                              callback_data=product['id'])])

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text('Please choose:', reply_markup=reply_markup)
    return "HANDLE_DESCRIPTION"


def handle_description(bot, update, access_token, client_id):
    """Хэндлер для обработки нажатия на кнопку."""
    query = update.callback_query
    chat_id = query.message.chat_id
    product_count = ''
    if 'кг' not in query.data:
        product_id = query.data
        product = fetch_product_by_id(access_token, product_id)
    else:
        data = query.data.replace('кг', '')
        product_count = data.split()[0]
        product_id = data.split()[1]
        product = fetch_product_by_id(access_token, product_id)
    product_attributes = product['data']['attributes']
    price_books = fetch_prices_book(access_token)
    price_id = 0
    for price_book in price_books['data']:
        if price_book['attributes']['name'] == product['data']['attributes']['name']:
            price_id = price_book['id']
    prices = fetch_product_prices(access_token, price_id)
    product_price = prices['data'][0]['attributes']['currencies']['USD']['amount']
    product_stock = fetch_product_stock(access_token, product_id)
    if product_count:
        put_product_to_branch(
            access_token, product, chat_id, client_id,
            product_price, product_count
        )
    try:
        photo_id = fetch_product_photo_by_id(access_token, product_id)
        photo = fetch_photo_by_id(access_token, photo_id)
    except TypeError:
        photo = "https://avatars.mds.yandex.net/i?id=cd502f949a596919c1b8feac39a0a5e4-5330065-images-thumbs&n=13"

    text = f"{product_attributes['name']}: \n\nцена {product_price / 100}$ за " \
           f"кг.\nостаток на складе {product_stock} кг.  " \
           f"\n\n{product_attributes['description']}"

    keyboard = []
    product_count_keyboard = [InlineKeyboardButton("1кг.", callback_data=f'1кг {product_id}'),
                              InlineKeyboardButton("5кг.", callback_data=f'5кг {product_id}'),
                              InlineKeyboardButton("10кг.", callback_data=f'10кг {product_id}')]
    keyboard.append(product_count_keyboard)
    products = fetch_products_branch(access_token, chat_id)
    if products.get('data'):
        keyboard.append(
            [InlineKeyboardButton(
                f"Корзина: {len(products.get('data'))} продукт(а/ов), на сумму: "
                f"{products['meta']['display_price']['with_tax']['formatted']}",
                callback_data='корзина'
            )]
        )
    else:
        keyboard.append([InlineKeyboardButton("Корзина пустая", callback_data='корзина')])
    keyboard.append([InlineKeyboardButton("Назад", callback_data='назад')])
    reply_markup = InlineKeyboardMarkup(keyboard)

    bot.send_photo(chat_id=query.message.chat_id, photo=photo, caption=text, reply_markup=reply_markup)
    bot.delete_message(chat_id=query.message.chat_id,
                       message_id=query.message.message_id)
    return "HANDLE_DESCRIPTION"


def handle_menu(bot, update, access_token, client_id):
    query = update.callback_query
    products = fetch_products(access_token)
    keyboard = []
    for product in products['data']:
        keyboard.append([InlineKeyboardButton(product['attributes']['name'],
                                              callback_data=product['id'])])

    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(chat_id=query.message.chat_id, text="Выберете дальнейшее действие:", reply_markup=reply_markup)
    bot.delete_message(chat_id=query.message.chat_id,
                       message_id=query.message.message_id)
    return "HANDLE_DESCRIPTION"


def handle_cart(bot, update, access_token, client_id):
    query = update.callback_query
    chat_id = query.message.chat_id
    if "удалить" in query.data:
        product_id = query.data.split()[1]
        remove_product_from_cart(access_token, chat_id, product_id)

    products_in_cart = fetch_products_branch(access_token, chat_id)
    cart_text = ''
    keyboard = []
    for product in products_in_cart['data']:
        keyboard.append(
            [InlineKeyboardButton(
                f"Убрать из корзины {product['name']}",
                callback_data=f"удалить {product['id']}"
            )]
        )
        prodect_text = f"{product['name']}:\n" \
                       f"Описание: {product['description']}\n" \
                       f"Кол-во: {product['quantity']}шт.\n" \
                       f"Цена: {product['meta']['display_price']['with_tax']['unit']['formatted']} за кг.\n" \
                       f"Стоймость позиции: {product['meta']['display_price']['with_tax']['value']['formatted']}\n\n"
        cart_text += prodect_text
    cart_text += f"Итоговая стоймость: {products_in_cart['meta']['display_price']['with_tax']['formatted']}"
    keyboard.append([InlineKeyboardButton('В меню', callback_data='назад')])
    keyboard.append([InlineKeyboardButton('Оплатить', callback_data='paid')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    if not products_in_cart['data']:
        cart_text = 'В данный момент ваша корзина пуста, вернитесь в главное ' \
                    'меню и сначала положите товар в корзину.'
    bot.send_message(chat_id=query.message.chat_id, text=cart_text, reply_markup=reply_markup)
    bot.delete_message(chat_id=query.message.chat_id,
                       message_id=query.message.message_id)
    return "HANDLE_CART"


def handle_paid(bot, update, access_token, client_id):
    query = update.callback_query

    text = 'Пришлите, пожалуйста, ваш емайл.'
    if update.message:
        chat_id = update.message.chat_id
        email = update.message.text
        username = update.effective_user.username
        client = create_client(access_token, username, email)

        text = f'Ваш емайл: {email}\n\nВерно?\n'
        keyboard = [
            [InlineKeyboardButton('Верно', callback_data='назад')],
            [InlineKeyboardButton('Не верно', callback_data='HANDLE_PAID')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)
        bot.delete_message(chat_id=chat_id, message_id=query.message.message_id)
        return "HANDLE_PAID"
    chat_id = query.message.chat_id
    bot.send_message(chat_id=chat_id, text=text)
    bot.delete_message(chat_id=chat_id, message_id=query.message.message_id)
    return "HANDLE_PAID"




def handle_users_reply(bot, update, access_token, client_id):
    """
    Функция, которая запускается при любом сообщении от пользователя и решает как его обработать.
    Эта функция запускается в ответ на эти действия пользователя:
        * Нажатие на inline-кнопку в боте
        * Отправка сообщения боту
        * Отправка команды боту
    Она получает стейт пользователя из базы данных и запускает соответствующую функцию-обработчик (хэндлер).
    Функция-обработчик возвращает следующее состояние, которое записывается в базу данных.
    Если пользователь только начал пользоваться ботом, Telegram форсит его написать "/start",
    поэтому по этой фразе выставляется стартовое состояние.
    Если пользователь захочет начать общение с ботом заново, он также может воспользоваться этой командой.
    """
    db = get_database_connection()
    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        user_reply = update.callback_query.data
        chat_id = update.callback_query.message.chat_id
    else:
        return
    if user_reply == '/start':
        user_state = 'START'
    elif user_reply == 'назад':
        user_state = 'HANDLE_MENU'
    elif 'корзина' in user_reply:
        user_state = 'HANDLE_CART'
    elif 'paid' in user_reply:
        user_state = "HANDLE_PAID"
    else:
        user_state = db.get(chat_id).decode("utf-8")
    
    states_functions = {
        'START': start,
        'HANDLE_MENU': handle_menu,
        'HANDLE_DESCRIPTION': handle_description,
        'HANDLE_CART': handle_cart,
        'HANDLE_PAID': handle_paid
    }
    state_handler = states_functions[user_state]
    try:
        next_state = state_handler(bot, update, access_token, client_id)
        db.set(chat_id, next_state)
    except Exception as err:
        print(err)


def get_database_connection():
    """
    Возвращает конекшн с базой данных Redis, либо создаёт новый, если он ещё не создан.
    """
    global _database
    if _database is None:
        database_password = env.str("REDIS_PASSWORD")
        database_host = env.str("REDIS_HOST")
        database_port = env.str("REDIS_PORT")
        _database = redis.Redis(host=database_host, port=database_port, password=database_password)
    return _database


if __name__ == '__main__':
    token = env.str("TG_API_TOKEN")
    client_id = env.str("CLIENT_ID")
    client_secret = env.str("SECRET_KEY")
    access_token = fetch_access_token(client_id, client_secret)
    updater = Updater(token)

    handle_users = partial(handle_users_reply, access_token=access_token, client_id=client_id)

    dispatcher = updater.dispatcher
    dispatcher.add_handler(CallbackQueryHandler(handle_users))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users))
    dispatcher.add_handler(CommandHandler('start', handle_users))

    updater.start_polling()