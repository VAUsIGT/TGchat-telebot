import telebot,os
from telebot import types
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from collections import deque
import logging

logging.basicConfig(level=logging.INFO)

# Ваш токен бота
TOKEN = "TOKEN"
bot = telebot.TeleBot(TOKEN)

# Очередь пользователей
search_queue = deque()
# Словарь активных пар {user_id: partner_id}
active_chats = {}

# Состояния пользователей: "idle", "searching", "chatting"
user_states = {}

def log_state():
    logging.info(f"Очередь: {list(search_queue)}")
    logging.info(f"Активные чаты: {active_chats}")

# Функция для создания клавиатуры
def create_keyboard(buttons):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    for button in buttons:
        keyboard.add(KeyboardButton(button))
    return keyboard

# Функция для обновления состояния пользователя
def update_state(user_id, state):
    user_states[user_id] = state
    if state == "idle":
        bot.send_message(user_id, "Нажмите /search, чтобы найти собеседника.",
                         reply_markup=create_keyboard(["/search"]))
    elif state == "searching":
        bot.send_message(user_id, "Вы добавлены в очередь. Ожидайте собеседника или остановите поиск - /unsearch.",
                         reply_markup=create_keyboard(["🎲","/unsearch"]))
    elif state == "chatting":
        bot.send_message(user_id, "Собеседник найден. Общайтесь!\n\n/stop, чтобы завершить диалог\n/new, чтобы начать новый поиск",
                         reply_markup=create_keyboard(["/stop", "/new"]))
    elif state == "admin":
        bot.send_message(user_id,
                         "Добро пожаловать в админку - /статистика /диалоги /выход",
                         reply_markup=create_keyboard(["/статистика", "/диалоги", "/выход"]))

# Функция для записи пола в файл
def save_gender(user_id, gender):
    os.makedirs("gender", exist_ok=True)
    with open(f"gender/{user_id}.txt", "w") as file:
        file.write(gender)

# Обработчик старта
@bot.message_handler(commands=['start'])
def start_handler(message):
    global user_states
    user_id = message.chat.id
    if user_states.get(user_id) in ["searching", "chatting"]:
        search_queue.remove(user_id)
        update_state(user_id, "idle")
    bot.send_message(user_id,
                     "😉 Привет, это бот для анонимного общения '1 на 1', наш бот находится в разработке, но мы постараемся как можно быстрее довести функционал до уровня лучших ботов.\n\nЧем мы лучше?\nМы не планируем делать какие-то функции платными:\n✅ Вы не должны подписываться на каналы для работы бота\n✅ Работает поиск по полу\n✅ Доступны все медиа (стикеры, видео и т.д.)")
    gender_markup = types.InlineKeyboardMarkup()
    gender_markup.add(types.InlineKeyboardButton("Мужской", callback_data="Мужской"))
    gender_markup.add(types.InlineKeyboardButton("Женский", callback_data="Женский"))
    bot.send_message(user_id, "Для начала выберите ваш пол:", reply_markup=gender_markup)

# Обработчик админ-панели
@bot.message_handler(func=lambda msg: msg.text == "/админ01")
def admin(message):
    user_id = message.chat.id
    if user_id == admin_id:
        update_state(user_id, "admin")

# Обработчик админ-запроса
@bot.message_handler(func=lambda msg: msg.text == "/статистика")
def admin(message):
    user_id = message.chat.id
    if user_id == admin_id:
        bot.send_message(user_id, f"За запуск:\nКоличество сообщений: {count_messages}\nКоличество диалогов: {count_dialogs}")
# Обработчик админ-запроса
@bot.message_handler(func=lambda msg: msg.text == "/диалоги")
def admin(message):
    user_id = message.chat.id
    if user_id == admin_id:
        bot.send_message(user_id, f"Очередь: {list(search_queue)}\nАктивные чаты: {active_chats}")
# Обработчик выхода админа
@bot.message_handler(func=lambda msg: msg.text == "/выход")
def admin_exit(message):
    user_id = message.chat.id
    if user_id == admin_id:
        bot.send_message(user_id, "Выход из админки")
        update_state(user_id, "idle")

# Обработчик кнопки "Поиск"
@bot.message_handler(func=lambda msg: msg.text == "/search")
def search_handler(message):
    global count_dialogs
    user_id = message.chat.id

    # Проверяем текущее состояние
    if user_states.get(user_id) in ["searching", "chatting"]:
        bot.send_message(user_id, "Вы уже ищете собеседника или общаетесь.")
        return

    # Добавляем пользователя в очередь и обновляем состояние
    search_queue.append(user_id)
    update_state(user_id, "searching")

    print("Пользователь зашёл в поиск")
    log_state()

    # Если в очереди больше одного человека, создаём пару
    if len(search_queue) > 1:

        user1 = search_queue.popleft()
        user2 = search_queue.popleft()

        active_chats[user1] = user2
        active_chats[user2] = user1

        update_state(user1, "chatting")
        update_state(user2, "chatting")

        count_dialogs+=1
        print("создание диалога для 2 человек")
        log_state()

# Обработчик кнопки "Остановить поиск"
@bot.message_handler(func=lambda msg: msg.text == "/unsearch")
def stop_search_handler(message):
    user_id = message.chat.id

    # Если пользователь не в поиске
    if user_states.get(user_id) != "searching":
        bot.send_message(user_id, "Вы не ищете собеседника. Нажмите /search", parse_mode="Markdown")
        update_state(user_id, "idle")
        return

    # Удаляем пользователя из очереди и обновляем состояние
    try:
        search_queue.remove(user_id)
        bot.send_message(user_id, "Вы вышли из поиска.")
        update_state(user_id, "idle")
        print("пользователь вышел из поиска")
        log_state()
    except:
        print("ошибка на 139")

# Обработчик сообщений в чате
@bot.message_handler(
    func=lambda msg: msg.chat.id in active_chats,
    content_types=[
        'text', 'photo', 'video', 'audio', 'document', 'sticker', 'voice', 'video_note', 'animation'
    ]
)
def chat_handler(message):
    global count_messages
    user_id = message.chat.id
    partner_id = active_chats.get(user_id)

    # Если сообщение — команда, перенаправляем на соответствующую функцию
    if message.text == "/stop":
        stop_chat_handler(message)
        return
    elif message.text == "/new":
        new_chat_handler(message)
        return

    # Если это обычное сообщение, пересылаем его партнёру
    if partner_id:
        # Пересылка сообщений
        try:
            if message.content_type == 'text':
                bot.send_message(partner_id, message.text)
            elif message.content_type == 'photo':
                bot.send_photo(partner_id, message.photo[-1].file_id, caption=message.caption)
            elif message.content_type == 'video':
                bot.send_video(partner_id, message.video.file_id, caption=message.caption)
            elif message.content_type == 'audio':
                bot.send_audio(partner_id, message.audio.file_id, caption=message.caption)
            elif message.content_type == 'document':
                bot.send_document(partner_id, message.document.file_id, caption=message.caption)
            elif message.content_type == 'sticker':
                bot.send_sticker(partner_id, message.sticker.file_id)
            elif message.content_type == 'voice':
                bot.send_voice(partner_id, message.voice.file_id, caption=message.caption)
            elif message.content_type == 'video_note':
                bot.send_video_note(partner_id, message.video_note.file_id)
            elif message.content_type == 'animation':
                bot.send_animation(partner_id, message.animation.file_id, caption=message.caption)
            else:
                bot.send_message(user_id, "Тип сообщения не поддерживается.")
        except Exception as e:
            bot.send_message(user_id, "Ошибка при отправке сообщения.")
            logging.error(f"Ошибка при пересылке сообщения {message.content_type}: {e}")

        count_messages+=1
        # Логирование
        logging.info(f"Переслано сообщение: {message.content_type} от {user_id} к {partner_id}")

# Обработчик кнопки "Стоп"
@bot.message_handler(func=lambda msg: msg.text == "/stop")
def stop_chat_handler(message):
    user_id = message.chat.id

    # Если пользователь не в активном чате
    if user_id not in active_chats:
        bot.send_message(user_id, "Вы не общаетесь с собеседником.")
        update_state(user_id, "idle")
        return

    # Завершаем диалог
    partner_id = active_chats.pop(user_id, None)
    if partner_id:
        try:
            active_chats.pop(partner_id, None)

            markup=types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("⚠️ Пожаловаться", callback_data="report"))
            bot.send_message(user_id, "Вы завершили диалог.", reply_markup=markup)
            bot.send_message(partner_id, "Ваш собеседник завершил диалог.", reply_markup=markup)

            # Обновляем состояние обоих пользователей
            update_state(user_id, "idle")
            update_state(partner_id, "idle")

            print("диалог завершён")
            log_state()
        except:
            print("ошибка на 225")

# Обработчик кнопки "Новый"
@bot.message_handler(func=lambda msg: msg.text == "/new")
def new_chat_handler(message):
    global count_dialogs
    user_id = message.chat.id

    # Если пользователь не в активном чате
    if user_id not in active_chats:
        bot.send_message(user_id, "Вы не общаетесь с собеседником.")
        update_state(user_id, "idle")
        return

    # Завершаем текущий диалог
    partner_id = active_chats.pop(user_id, None)
    if partner_id:
        active_chats.pop(partner_id, None)

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⚠️ Пожаловаться", callback_data="report"))
        bot.send_message(user_id, "Вы завершили диалог.", reply_markup=markup)
        bot.send_message(partner_id, "Ваш собеседник завершил диалог.", reply_markup=markup)
        update_state(partner_id, "idle")

        print("диалог завершён")
        log_state()

    # Добавляем пользователя в очередь для нового поиска
    search_queue.append(user_id)
    update_state(user_id, "searching")

    print("Пользователь зашёл в поиск")
    log_state()

    # Если в очереди больше одного человека, создаём пару
    if len(search_queue) > 1:
        user1 = search_queue.popleft()
        user2 = search_queue.popleft()

        active_chats[user1] = user2
        active_chats[user2] = user1

        update_state(user1, "chatting")
        update_state(user2, "chatting")

        count_dialogs+=1
        print("создание диалога для 2 человек")
        log_state()

# Обработчик сообщений вне диалога
@bot.message_handler(func=lambda msg: msg.chat.id not in active_chats and user_states.get(msg.chat.id) != "searching")
def not_in_dialog_handler(message):
    user_id = message.chat.id
    bot.send_message(user_id, "Вы не находитесь в диалоге. Нажмите /search чтобы найти собеседника.", parse_mode="Markdown")

#обработка пола и жалоб
@bot.callback_query_handler(func=lambda callback:True)
def callback_message(callback):
    global report_user
    if callback.data=="report":
        try:
            bot.send_message(callback.message.chat.id, "⚠️Прикрепите скриншот того, на что вы жалуетесь или возвращайтесь к поиску и ваша жалоба будет отменена⚠️")
            report_user=callback.message.chat.id # id подьзователя, от которого ожидается скрин
            bot.delete_message(callback.message.chat.id, callback.message.message_id)
        except:
            print("ошибка на 292")
    elif callback.data == "Мужской" or "Женский":
        gender = "male" if callback.data == "Мужской" else "female"
        user_id = callback.message.chat.id
        save_gender(user_id, gender)
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        bot.send_message(user_id, f"Ваш пол ({callback.data}) сохранён.")
        update_state(user_id, "idle")

#обработка фото от последнего юзера с жалобой
@bot.message_handler(
    func=lambda msg: msg.chat.id not in active_chats, content_types=['photo'])
def img_report(message):
    global report_user
    if message.chat.id == report_user:
        bot.send_photo(admin_id, message.photo[-1].file_id, caption=message.caption)
        bot.send_message(admin_id, f"жалоба от: {message.chat.id}")
        bot.send_message(message.chat.id, "Фото отправлено на рассмотрение")
        report_user=0

report_user=0 #id юзера, подавшего жалобу
admin_id=None #id с расширенными командами
count_messages=0 #число сообщений за запуск
count_dialogs=0 #число диалогов за запуск
print("-------------------бот запущен---------------------")
# Запуск бота
bot.polling()
