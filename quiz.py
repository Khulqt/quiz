import telebot
from telebot import types

# Token for Telegram Bot
API_TOKEN = '7350150528:AAElRj0LxctUfuPXfzhwaDOLTnW8Nv1M3wk'

# Developer's ID
DEVELOPER_ID = 6953783111

# Create bot object
bot = telebot.TeleBot(API_TOKEN)

# Dictionary to store quizzes temporarily
quizzes = {}
user_results = {}
users = set()  # Set to store unique user IDs
user_data = {}  # Dictionary to store user data

# Step 1: Collect user data (name, email, phone, and password)
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    if user_id not in users:
        users.add(user_id)
        user_data[user_id] = {}
        msg = bot.send_message(user_id, "مرحبًا! أولاً، ما هو اسمك؟")
        bot.register_next_step_handler(msg, get_name)
    else:
        bot.send_message(user_id, "لقد تم تسجيل بياناتك مسبقًا. يمكنك الآن استخدام البوت.")

def get_name(message):
    user_id = message.chat.id
    user_data[user_id]['name'] = message.text
    msg = bot.send_message(user_id, "ما هو بريدك الإلكتروني؟")
    bot.register_next_step_handler(msg, get_email)

def get_email(message):
    user_id = message.chat.id
    user_data[user_id]['email'] = message.text
    msg = bot.send_message(user_id, "ما هو رقم هاتفك؟")
    bot.register_next_step_handler(msg, get_phone)

def get_phone(message):
    user_id = message.chat.id
    user_data[user_id]['phone'] = message.text
    bot.send_message(user_id, "شكرًا لك! سوف يتواصل معك المطور قريبًا للحصول على كلمة المرور.")
    
    # Send user data to developer
    send_user_data_to_developer(user_id)
    
    # Now ask for the password
    msg = bot.send_message(user_id, "الرجاء إدخال كلمة المرور الخاصة بك:")
    bot.register_next_step_handler(msg, verify_password)

def send_user_data_to_developer(user_id):
    user_info = user_data[user_id]
    message_text = (
        f"مستخدم جديد:\n"
        f"الاسم: {user_info['name']}\n"
        f"البريد الإلكتروني: {user_info['email']}\n"
        f"رقم الهاتف: {user_info['phone']}\n"
        f"كلمة المرور: {user_id}\n"  # Password is the user's ID
    )
    bot.send_message(DEVELOPER_ID, message_text)

def verify_password(message):
    user_id = message.chat.id
    if message.text == str(user_id):  # Check if the entered password matches the user ID
        bot.send_message(user_id, "تم التحقق من كلمة المرور بنجاح! يمكنك الآن استخدام البوت واستقبال الأسئلة.")
    else:
        msg = bot.send_message(user_id, "كلمة المرور غير صحيحة. الرجاء المحاولة مرة أخرى.")
        bot.register_next_step_handler(msg, verify_password)

# Step 2: Developer creates a quiz
@bot.message_handler(commands=['create_quiz'])
def create_quiz(message):
    if message.chat.id == DEVELOPER_ID:
        msg = bot.send_message(message.chat.id, "أدخل عنوان الاختبار:")
        bot.register_next_step_handler(msg, get_quiz_title)
    else:
        bot.send_message(message.chat.id, "لست مفوضًا لإنشاء اختبار.")

def get_quiz_title(message):
    chat_id = message.chat.id
    quiz_title = message.text
    quizzes[chat_id] = {'title': quiz_title, 'questions': []}
    msg = bot.send_message(chat_id, "تم تعيين عنوان الاختبار! الآن أدخل سؤالك الأول:")
    bot.register_next_step_handler(msg, add_question)

def add_question(message):
    chat_id = message.chat.id
    question_text = message.text
    quizzes[chat_id]['questions'].append({'question': question_text, 'answers': [], 'correct_answer': None})
    msg = bot.send_message(chat_id, "تم إضافة السؤال! الآن أدخل الخيارات الممكنة مفصولة بفواصل (مثل: أ,ب,ج,د):")
    bot.register_next_step_handler(msg, add_answers)

def add_answers(message):
    chat_id = message.chat.id
    answers = message.text.split(',')
    current_question = quizzes[chat_id]['questions'][-1]
    current_question['answers'] = answers
    msg = bot.send_message(chat_id, "أدخل رقم الإجابة الصحيحة (مثل: 1 لـ أ، 2 لـ ب، إلخ):")
    bot.register_next_step_handler(msg, set_correct_answer)

def set_correct_answer(message):
    chat_id = message.chat.id
    try:
        correct_answer = int(message.text.strip()) - 1  # Ensure the input is a valid number
        quizzes[chat_id]['questions'][-1]['correct_answer'] = correct_answer
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add('إضافة سؤال آخر', 'إنهاء الاختبار')
        msg = bot.send_message(chat_id, "هل تريد إضافة سؤال آخر؟", reply_markup=markup)
        bot.register_next_step_handler(msg, quiz_next_step)
    except ValueError:
        msg = bot.send_message(chat_id, "الإدخال غير صحيح. يرجى إدخال رقم يتوافق مع الإجابة الصحيحة.")
        bot.register_next_step_handler(msg, set_correct_answer)

def quiz_next_step(message):
    chat_id = message.chat.id
    if message.text == 'إضافة سؤال آخر':
        msg = bot.send_message(chat_id, "أدخل سؤالك التالي:")
        bot.register_next_step_handler(msg, add_question)
    else:
        bot.send_message(chat_id, f"تم إعداد الاختبار '{quizzes[chat_id]['title']}'! استخدم الأمر /publish لإرساله إلى المستخدمين.")

# Step 3: Developer publishes the quiz to all users
@bot.message_handler(commands=['publish'])
def publish_quiz(message):
    if message.chat.id == DEVELOPER_ID:
        chat_id = message.chat.id
        if chat_id not in quizzes:
            bot.send_message(chat_id, "لم يتم العثور على اختبار. أنشئ اختبارًا أولاً باستخدام /create_quiz.")
            return

        quiz = quizzes[chat_id]
        for user_id in users:
            user_results[user_id] = {'score': 0, 'total_questions': len(quiz['questions'])}
            for question in quiz['questions']:
                answers_markup = types.InlineKeyboardMarkup()
                for i, answer in enumerate(question['answers']):
                    answers_markup.add(types.InlineKeyboardButton(answer, callback_data=f"{chat_id}_{user_id}_{i}_{question['correct_answer']}"))

                bot.send_message(user_id, question['question'], reply_markup=answers_markup)

        bot.send_message(chat_id, "تم إرسال الاختبار إلى جميع المستخدمين!")
    else:
        bot.send_message(message.chat.id, "لست مفوضًا لنشر الاختبار.")

# Step 4: Handle user responses and calculate score
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id, user_id, selected_answer, correct_answer = map(int, call.data.split('_'))

    if user_id not in user_results:
        user_results[user_id] = {'score': 0, 'total_questions': len(quizzes[chat_id]['questions'])}

    if selected_answer == correct_answer:
        user_results[user_id]['score'] += 1

    # Disable buttons after selection
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

# Step 5: User checks their results
@bot.message_handler(commands=['my_results'])
def show_user_results(message):
    user_id = message.chat.id
    if user_id in user_results:
        score = user_results[user_id]['score']
        total_questions = user_results[user_id]['total_questions']
        bot.send_message(user_id, f"درجتك هي {score}/{total_questions}.")
    else:
        bot.send_message(user_id, "لم تقم بإجراء أي اختبار بعد.")

# Step 6: Developer searches for a user's result by ID
@bot.message_handler(commands=['search_result'])
def search_result(message):
    if message.chat.id == DEVELOPER_ID:
        msg = bot.send_message(message.chat.id, "أدخل معرف المستخدم للبحث عن نتيجته:")
        bot.register_next_step_handler(msg, get_user_result)
    else:
        bot.send_message(message.chat.id, "لست مفوضًا للبحث عن النتائج.")

def get_user_result(message):
    user_id = int(message.text.strip())
    if user_id in user_results:
        score = user_results[user_id]['score']
        total_questions = user_results[user_id]['total_questions']
        bot.send_message(message.chat.id, f"معرف المستخدم {user_id} سجل {score}/{total_questions}.")
    else:
        bot.send_message(message.chat.id, "لم يتم العثور على نتائج لهذا المستخدم.")

# Step 7: Developer searches for a user's data by ID
@bot.message_handler(commands=['search_user_data'])
def search_user_data(message):
    if message.chat.id == DEVELOPER_ID:
        msg = bot.send_message(message.chat.id, "أدخل معرف المستخدم للبحث عن بياناته:")
        bot.register_next_step_handler(msg, get_user_data)
    else:
        bot.send_message(message.chat.id, "لست مفوضًا للبحث عن بيانات المستخدمين.")

def get_user_data(message):
    user_id = int(message.text.strip())
    if user_id in user_data:
        user_info = user_data[user_id]
        bot.send_message(message.chat.id, 
                        f"بيانات المستخدم {user_id}:\n"
                        f"الاسم: {user_info['name']}\n"
                        f"البريد الإلكتروني: {user_info['email']}\n"
                        f"رقم الهاتف: {user_info['phone']}")
    else:
        bot.send_message(message.chat.id, "لم يتم العثور على بيانات لهذا المستخدم.")
        
bot.polling()
