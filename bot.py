import logging
import sys
import os

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger()

MODE = os.getenv("MODE")
TOKEN = os.getenv("TOKEN")
PORT = int(os.environ.get('PORT', '8443'))
HEROKU_APP_NAME = os.getenv("HEROKU_APP_NAME")

def run(updater):
    if MODE == "dev":
        updater.start_polling()
    elif MODE == "prod":
        updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN)
        updater.bot.set_webhook("https://{}.herokuapp.com/{}".format(HEROKU_APP_NAME, TOKEN))
    else:
        logger.error("需要设置 MODE!")
        sys.exit(1)

def start(update, context):
    update.message.reply_text('欢迎使用! 🎉')

def echo(update, context):
    update.message.reply_text(update.message.text)

def error(update, context):
    logger.warning('Update "%s" 出现错误 "%s"', update, context.error)

if __name__ == '__main__':
    if MODE == "dev":
        updater = Updater(TOKEN, use_context=True, request_kwargs={
            'proxy_url': 'socks5h://127.0.0.1:7891/'
        })
    elif MODE == "prod":
        updater = Updater(TOKEN, use_context=True)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text, echo))
    dp.add_error_handler(error)

    run(updater)

    updater.idle()