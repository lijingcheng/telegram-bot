import logging
import sys
import os
import json
import smtplib
import asyncio
import schedule
import time
from email.mime.text import MIMEText
from email.utils import formataddr
from email.mime.multipart import MIMEMultipart

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, Filters

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger()

DATA_FILE_NAME = 'data.json'
MODE = os.getenv("MODE")
TOKEN = os.getenv("TOKEN")
PORT = int(os.environ.get('PORT', '8443'))
HEROKU_APP_NAME = os.getenv("HEROKU_APP_NAME")
WHITE_LIST = os.getenv("WHITE_LIST")

def sendmail(subject, content, to):
    email = MIMEMultipart()
    email.attach((MIMEText(content, 'html', 'utf-8')))
    email['Subject'] = subject
    email['From'] = formataddr(["李京城", 'bj_lijingcheng@163.com'])
    email['To'] = formataddr([to, to])

    smtp = smtplib.SMTP()
    smtp.connect('smtp.163.com', 25)
    smtp.login('bj_lijingcheng', os.getenv("EMAIL_PASS"))
    smtp.sendmail('bj_lijingcheng@163.com', [to], email.as_string())
    smtp.quit()

def readFile(file):
    try:
        with open(file, 'r') as handle:
            data = json.load(handle)
            handle.close()

            if data:
                return data
            else:
                return {}
    except FileNotFoundError:
        file = open(DATA_FILE_NAME, 'w')
        file.close()
        return {}

async def writeToFile(file, dict):
    with open(file, 'w') as handle: # w 表示每次写时覆盖原内容
        json.dump(dict, handle)
        handle.write("\n")
        handle.close()

def dailyRemind():
    sendmail('日报提醒', '<p>你好：</p><p>五点前需要提交日报！</p>', 'jingcheng.li@mtime.com')

    data = readFile(DATA_FILE_NAME)

    for key, value in data.items():
        if 'subscription' in value:
            subscription = value['subscription']

            for i, val in enumerate(subscription):
                if val == '1': # 日报
                    updater.bot.send_message(chat_id=key, text='你好，五点前需要提交日报！')

def weeklyRemind():
    sendmail('周报提醒', '<p>你好：</p><p>三点前需要提交周报！</p>', 'jingcheng.li@mtime.com')

    data = readFile(DATA_FILE_NAME)

    for key, value in data.items():
        if 'subscription' in value:
            subscription = value['subscription']

            for i, val in enumerate(subscription):
                if val == '2': # 周报
                    updater.bot.send_message(chat_id=key, text='你好，三点前需要提交周报！')

def start(update, context):
    update.message.reply_text('欢迎使用 🎉')

def account(update, context):
    if update._effective_user.username in WHITE_LIST:
        content = ''
        for item in os.getenv("WANDAFILM_ACCOUNT").split(','):
            content += (item + '\n')

        update.message.reply_text(content)
    else:
        update.message.reply_text('仅支持万达电影 iOS 团队开发人员使用')

def echo(update, context):
    if update.message.text == 'fuck':
        update.message.reply_text('Did you mean fuck you?')
    else:
        pass

def unknown(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="不支持此命令./help")

def subscription(update, context):
    keyboard = [[InlineKeyboardButton("日报提醒", callback_data='1'), InlineKeyboardButton("周报提醒", callback_data='2')]]

    update.message.reply_text('订阅:', reply_markup=InlineKeyboardMarkup(keyboard))

# 用户会对应一些业务，每个业务对应该用户的选择
def subscriptionCallback(update, context):
    query = update.callback_query
    query.edit_message_text(text="订阅成功 🎉")

    chatId = str(query.message.chat.id)

    data = readFile(DATA_FILE_NAME)

    if chatId in data.keys():
        userData = data[chatId]

        if 'subscription' in userData:
            userSubscription = userData['subscription']

            if query.data not in userSubscription:
                userSubscription.append(query.data)
                data[chatId]['subscription'] = userSubscription
        else:
            data[chatId].append({'subscription': [query.data]})
    else:
        data[chatId] = {'subscription': [query.data]}

    asyncio.run(writeToFile(DATA_FILE_NAME, data))

def new_members(update, context):
    for member in update.message.new_chat_members:
        if member.username == updater.bot.username:
            update.message.reply_text('谢谢邀请 🎉')
        else:
            update.message.reply_text("欢迎 {} 🎉".format(member.username))

def left_member(update, context):
    update.message.reply_text("再见 {}".format(update.message.left_chat_member.username))

def error(update, context):
    logger.warning('"%s" 出现错误 "%s"', update, context.error)

if __name__ == '__main__':
    if MODE == "dev":
        updater = Updater(TOKEN, use_context=True, request_kwargs={
            'proxy_url': 'socks5h://127.0.0.1:1086' # 如果你需要翻墙才能使用 telegram 需要设置 vpn 软件中使用的代理设置
        })
    elif MODE == "prod":
        updater = Updater(TOKEN, use_context=True)
    else:
        logger.error("需要设置 MODE!")
        sys.exit(1)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("account", account))
    dp.add_handler(CommandHandler("subscription", subscription))
    dp.add_handler(CallbackQueryHandler(subscriptionCallback))

    dp.add_handler(MessageHandler(Filters.text, echo))
    dp.add_handler(MessageHandler(Filters.command, unknown))
    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, new_members))
    dp.add_handler(MessageHandler(Filters.status_update.left_chat_member, left_member))

    dp.add_error_handler(error)

    if MODE == "dev":
        updater.start_polling()
    elif MODE == "prod":
        updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN)
        updater.bot.set_webhook("https://{}.herokuapp.com/{}".format(HEROKU_APP_NAME, TOKEN))

    schedule.every().friday.at("03:00").do(weeklyRemind)

    while True:
        schedule.run_pending()
        time.sleep(1)

    updater.idle()
