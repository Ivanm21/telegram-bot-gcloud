import os
import logging

import telegram
from telegram.ext import Dispatcher
from telegram.ext import MessageHandler, Filters


project_id = '122310846920'
secret_id = 'TELEGRAM_TOKEN'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

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

def echo(update, context):
    text_to_send = f'What do you mean: {update.message.text}?'
    context.bot.sendMessage(chat_id=update.effective_chat.id, text=text_to_send)


def setup(bot):
    # Create bot, update queue and dispatcher instances
    
    dispatcher = Dispatcher(bot, None, workers=0)
    
    ##### Register handlers here #####
    echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
    dispatcher.add_handler(echo_handler)

    
    return dispatcher


def webhook(request):

    token = access_secret_version(project_id,secret_id )
    bot = telegram.Bot(token=token)

    dispatcher = setup(bot)
    
    if request.method == "POST":
        update = telegram.Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
    
    return 'ok'
    



