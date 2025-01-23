print("-------------------подготовка----------------------")
import settings
import telebot,os
from telebot import types
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from collections import deque
import logging
import time

#сделано: общие баны, рассылка, фиксы с блоком бота, стоп в поиске, смена пола вне простоя,

#сделать: личные блокировки юзеров от пользователя, клавиатуру обновить, поиск по полу, логи в txt, индивидуальные сообщения.
#пофиксить: репорт вне ожидания, репорт должен исчезать после любого действия чтобы нельзя было отправлять несколько (стоит репорт отдельным состоянием сделать)

logging.basicConfig(level=logging.INFO)

# Ваш токен бота
TOKEN = apitoken.token
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
                         "Добро пожаловать в админку:\n/статистика\n/диалоги\n/анонс [сообщение пользователям]\n/бан [id]\n/выход",
                         reply_markup=create_keyboard(["/статистика", "/диалоги", "/выход"]))

#загрузка забаненых из txt
def load_banned_users():
    global banned_users
    try:
        # Открываем файл на чтение
        with open("banned_users.txt", "r") as file:
            # Считываем строки, удаляем лишние пробелы и перевод строки
            banned_users = [int(line.strip()) for line in file if line.strip().isdigit()]
        print(f"Загружено {len(banned_users)} заблокированных пользователей: {banned_users}")
    except FileNotFoundError:
        print("Файл banned_users.txt не найден. Список заблокированных пользователей пуст.")
    except Exception as e:
        print(f"Ошибка при загрузке списка заблокированных пользователей: {e}")
# Функция для добавления пользователя в список и файл -   бан
def ban_user(user_id):
    global banned_users
    if user_id in banned_users:
        return False  # Пользователь уже заблокирован
    banned_users.append(user_id)
    try:
        with open("banned_users.txt", "a") as file:
            file.write(f"{user_id}\n")
        print(f"Пользователь {user_id} добавлен в список заблокированных.")
        return True
    except Exception as e:
        print(f"Ошибка при добавлении пользователя в файл: {e}")
        return False

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
    print(f"пользователь {user_id} запустил бота")
    if user_states.get(user_id) in ["searching"]:
        search_queue.remove(user_id)
        update_state(user_id, "idle")
    if user_id in active_chats:
        active_chats.pop(user_id, None)
        update_state(user_id, "idle")
    bot.send_message(user_id,
                     "😉 Привет, это бот для анонимного общения '1 на 1', наш бот находится в разработке, но мы постараемся как можно быстрее довести функционал до уровня лучших ботов.\n\nЧем мы лучше?\nМы не планируем делать какие-то функции платными:\n✅ Вы не должны подписываться на каналы для работы бота\n✅ Работает поиск по полу\n✅ Доступны все медиа (стикеры, видео и т.д.).\nПеред использованием прочитай правила - /rules, если что-то не так - /help")
    gender_markup = types.InlineKeyboardMarkup()
    gender_markup.add(types.InlineKeyboardButton("Мужской", callback_data="Мужской"))
    gender_markup.add(types.InlineKeyboardButton("Женский", callback_data="Женский"))
    bot.send_message(user_id, "Для начала выберите ваш пол:", reply_markup=gender_markup)
    update_state(user_id, "idle")

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
        bot.send_message(user_id, f"Очередь: \n{list(search_queue)}\nАктивные чаты: \n{active_chats}")
@bot.message_handler(func=lambda msg: msg.text[:6] == "/анонс")
def send_announcement(message):
    user_id = message.chat.id
    if user_id == admin_id:
        # Проверяем, есть ли текст для анонса
        if len(message.text.split(' ', 1)) < 2:
            bot.send_message(message.chat.id, "Пожалуйста, укажите текст анонса после команды /анонс.")
            return
        announcement_text = message.text.split(' ', 1)[1]
        # Папка с ID пользователей
        genders_folder = "gender"
        if not os.path.exists(genders_folder):
            bot.send_message(admin_id, "Папка с пользователями пуста или не существует.")
            return
        user_ids = []
        try:
            # Считываем все ID пользователей из файлов
            for filename in os.listdir(genders_folder):
                if filename.endswith(".txt"):
                    user_id = filename.split(".")[0]
                    if user_id.isdigit():
                        user_ids.append(int(user_id))
        except Exception as e:
            bot.send_message(admin_id, f"Ошибка чтения папки с пользователями: {e}")
            return
        # Отправляем сообщение всем пользователям
        sent_count = 0
        for user_id in user_ids:
            try:
                bot.send_message(user_id, announcement_text)
                sent_count += 1
            except Exception as e:
                logging.error(f"Не удалось отправить сообщение пользователю {user_id}: {e}")
        bot.send_message(admin_id, f"Анонс отправлен {sent_count} пользователям.")
# Команда для блокировки пользователя
@bot.message_handler(func=lambda msg: msg.text[:4] == "/бан")
def ban_command_handler(message):
    user_id = message.chat.id
    if user_id == admin_id:
        # Разделяем текст команды на части
        parts = message.text.split()
        if len(parts) != 2:
            bot.send_message(message.chat.id, "Использование: /бан <ID пользователя>")
            return
        try:
            # Преобразуем ID в число
            user_id = int(parts[1])
            # Блокируем пользователя
            if ban_user(user_id):
                bot.send_message(message.chat.id, f"Пользователь {user_id} успешно заблокирован.")
            else:
                bot.send_message(message.chat.id, f"Пользователь {user_id} уже заблокирован.")
        except ValueError:
            bot.send_message(message.chat.id, "ID пользователя должно быть числом.")
        except Exception as e:
            bot.send_message(message.chat.id, f"Произошла ошибка: {e}")
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
    global report_user
    global count_dialogs
    user_id = message.chat.id
    #для пользователей в бане
    if user_id in banned_users:
        bot.send_message(user_id, "Вы заблокированны в нашем боте")
        return

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
# Обработчик команды /help
@bot.message_handler(func=lambda msg: msg.text == "/help")
def search_handler(message):
    user_id = message.chat.id
    bot.send_message(user_id, "Если что-то не так с ботом, то должен помочь перезапуск - /start\nВне диалога работает только команда /search\nВ диалоге команды /stop и /new\nВо время поиска - /unsearch и кнопка броска кубика (мини игра)\nТакже, если что-то не так с собеседником, вы можете пожаловаться на него после диалога\n\nПо всем вопросам обращаться к @Farquad_on_quad\n🔥 Приятного общения!")
@bot.message_handler(func=lambda msg: msg.text == "/rules")
def search_handler(message):
        user_id = message.chat.id
        bot.send_message(user_id, "📌 Правила общения в анонимном чате:\n1. Любые упоминания психоактивных веществ (наркотиков)\n2. Обсуждение политики\n3. Детская порнография ('ЦП')\n4. Мошенничество (Scam)\n5. Любая реклама, спам\n6. Рассовая, половая, сексуальная, и любая другая дискриминация\n7. Продажи чего либо (например - продажа интимных фотографий, видео)\n8. Любые действия, нарушающие правила Telegram\n9. Оскорбительное поведение\n❌ За нарушение правил - блокировка аккаунта")
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
        print("ошибка на 251")

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
        logging.info(f"Переслано сообщение: {message.content_type} от {user_id} к {partner_id}:\n {message.text}")

# Обработчик кнопки "Стоп"
@bot.message_handler(func=lambda msg: msg.text == "/stop")
def stop_chat_handler(message):
    user_id = message.chat.id

    # Если пользователь не в активном чате
    if user_states.get(user_id) in ["searching", "idle"]:
        bot.send_message(user_id, "Вы не общаетесь с собеседником.")
        return

    # Завершаем диалог
    partner_id = active_chats.pop(user_id, None)
    if partner_id:
        try:
            active_chats.pop(partner_id, None)

            markup=types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("⚠️ Пожаловаться", callback_data="report"))
            bot.send_message(user_id, "Вы завершили диалог.", reply_markup=markup)
            update_state(user_id, "idle")
            #защита от блокировки
            try:
                bot.send_message(partner_id, "Ваш собеседник завершил диалог.", reply_markup=markup)
            except:
                print(F"Пользователь {partner_id} заблокировал бота")
            update_state(partner_id, "idle")

            print("диалог завершён")
            log_state()
        except:
            print("ошибка на 339")

# Обработчик кнопки "Новый"
@bot.message_handler(func=lambda msg: msg.text == "/new")
def new_chat_handler(message):
    global count_dialogs
    user_id = message.chat.id

    # Если пользователь не в активном чате
    if user_states.get(user_id) in ["searching", "idle"]:
        bot.send_message(user_id, "Вы не общаетесь с собеседником.")
        return
    update_state(user_id, "searching")
    # Завершаем текущий диалог
    partner_id = active_chats.pop(user_id, None)
    if partner_id:
        active_chats.pop(partner_id, None)

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⚠️ Пожаловаться", callback_data="report"))
        bot.send_message(user_id, "Вы завершили диалог.", reply_markup=markup)
        try:
            bot.send_message(partner_id, "Ваш собеседник завершил диалог.", reply_markup=markup)
        except:
            print(f"Пользователь {partner_id} заблокировал бота")
        update_state(partner_id, "idle")

        print("диалог завершён")
        log_state()

    # Добавляем пользователя в очередь для нового поиска
    search_queue.append(user_id)

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
    global report_user
    user_id = message.chat.id
    if user_id == report_user:
        bot.send_message(admin_id, f"жалоба от: {message.chat.id}\nсообщение: {message.text}")
        bot.send_message(user_id, "Жалоба отправлена на рассмотрение")
        report_user = 0
    else:
        bot.send_message(user_id, "Вы не находитесь в диалоге. Нажмите /search чтобы найти собеседника.", parse_mode="Markdown")

#обработка пола и жалоб
@bot.callback_query_handler(func=lambda callback:True)
def callback_message(callback):
    global report_user
    if callback.data=="report":
        try:
            if user_states.get(callback.message.chat.id) in ["searching","chatting"]:
                return
            bot.send_message(callback.message.chat.id, "⚠️Прикрепите скриншот того, на что вы жалуетесь ИЛИ напишите текстом, либо возвращайтесь к поиску и ваша жалоба будет отменена⚠️")
            report_user=callback.message.chat.id # id подьзователя, от которого ожидается скрин
            bot.delete_message(callback.message.chat.id, callback.message.message_id)
        except:
            print("ошибка на 412")
    elif callback.data == "Мужской" or "Женский":
        gender = "male" if callback.data == "Мужской" else "female"
        user_id = callback.message.chat.id
        save_gender(user_id, gender)
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        bot.send_message(user_id, f"Ваш пол ({callback.data}) сохранён.")

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

banned_users=[] #список забаненых
load_banned_users() #подгруз txt
report_user=0 #id юзера, подавшего жалобу
admin_id=settings.admin #id с расширенными командами
count_messages=0 #число сообщений за запуск
count_dialogs=0 #число диалогов за запуск
print("------------------бот загружен---------------------")

# Запуск бота
def run():
    global timer
    try:
        bot.polling()
        print("работа прекращена")
    except:
        if timer<320:
            timer*=2
            print(f"ошибка запуска, повтор через: {timer}")
            time.sleep(timer)
            run()
        else:
            print("попытки подключиться прекращены")
            return
timer=5
#bot.polling()
run()