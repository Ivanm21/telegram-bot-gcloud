import os
import logging

import telegram
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import Dispatcher
from telegram.ext import (CommandHandler, MessageHandler, Filters, ConversationHandler,  PicklePersistence)


project_id = '122310846920'
secret_id = 'TELEGRAM_TOKEN'

def access_secret_version(project_id, secret_id, version_id='latest'):
    """
    Access the payload for the given secret version if one exists. The version
    can be a version number as a string (e.g. "5") or an alias (e.g. "latest").
    """

    # Import the Secret Manager client library.
    from google.cloud import secretmanager

    # Create the Secret Manager client.
    client = secretmanager.SecretManagerServiceClient()

    # Build the resource name of the secret version.
    name = client.secret_version_path(project_id, secret_id, version_id)

    # Access the secret version.
    response = client.access_secret_version(name)

    # Print the secret payload.
    #
    # WARNING: Do not print the secret in a production environment - this
    # snippet is showing how to access the secret material.
    payload = response.payload.data.decode('UTF-8')
    return payload



logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.DEBUG)

logger = logging.getLogger(__name__)


CHOOSING, TYPING_REPLY, TYPING_CHOICE = range(3)

reply_keyboard = [['Возраст', 'Любимый цвет'],
                  ['Имя', 'Фамилия'],
                  ['Все']]

markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)


def echo(update, context):
    text_to_send = f'{update.message.text}'
    context.bot.send_message(chat_id=update.effective_chat.id, text=text_to_send)

def facts_to_str(user_data):
    facts = list()

    for key, value in user_data.items():
        facts.append('{} - {}'.format(key, value))

    return "\n".join(facts).join(['\n', '\n'])


def start(update, context):
    
    update.message.reply_text(
        'Привет! Шо там, давай рассказывай. '
        'Отправь /cancel что бы закончить .\n\n',
        reply_markup=markup)
         

    return CHOOSING

def regular_choice(update, context):
    text = update.message.text
    context.user_data['choice'] = text
    update.message.reply_text(
        'Категория {}/n'
        'Теперь введи значение'.format(text.lower()))

    return TYPING_REPLY

def custom_choice(update, context):
    update.message.reply_text('Как хочешь. Тогда отправь категорию. '
                              'например "Имя моего пса"')

    return TYPING_CHOICE

def received_information(update, context):
    user_data = context.user_data
    text = update.message.text
    category = user_data['choice']
    user_data[category] = text
    del user_data['choice']

    update.message.reply_text("Ок. Вот что ты мне уже известно:"
                              "{} можешь рассказать еще или поменять что то".format(facts_to_str(user_data)),
                              reply_markup=markup)

    return CHOOSING

def done(update, context):
    user_data = context.user_data
    if 'choice' in user_data:
        del user_data['choice']

    update.message.reply_text("Я знаю про тебя следующее"
                              "{}"
                              "Давай, пока!".format(facts_to_str(user_data)))

    user_data.clear()
    return ConversationHandler.END

def cancel(update, context):
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text('Давай, пока!',
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END

def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def setup(token):
    # Create bot, update queue and dispatcher instances
    pp = PicklePersistence(filename='conversationbot')

    bot = telegram.Bot(token=token)
    dispatcher = Dispatcher(bot, None, workers=0, use_context=True, persistence=pp)


    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            CHOOSING: [MessageHandler(Filters.regex('^(Age|Favourite colour|Number of siblings)$'),
                                      regular_choice),
                       MessageHandler(Filters.regex('^Something else...$'),
                                      custom_choice)
                       ],

            TYPING_CHOICE: [MessageHandler(Filters.text,
                                           regular_choice)
                            ],

            TYPING_REPLY: [MessageHandler(Filters.text,
                                          received_information),
                           ],
        },

        fallbacks=[CommandHandler('cancel', cancel),
                    MessageHandler(Filters.regex('^Done$'), done)], 
        name='my_conversation', 
        persistent=True
    )

    dispatcher.add_handler(conv_handler)

    # log all errors
    dispatcher.add_error_handler(error)
       
    return dispatcher


def webhook(request):

    if request.method == "POST":
        update = telegram.Update.de_json(request.get_json(force=True), dispatcher.bot)
        dispatcher.process_update(update)
    
    return 'ok'
    

token = access_secret_version(project_id,secret_id )
dispatcher  = setup(token)
