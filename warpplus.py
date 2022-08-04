#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2022/07/27
# @Author  : Oreomeow
# @File    : warpplus.py
# @Software: PyCharm
import datetime
import json
import logging
import os
import random
import re
import string
import time
import urllib.request

from telegram import Update
from telegram.ext import CallbackContext, CommandHandler, Updater

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

with open("Config/config.json", "r") as f:
    config = json.load(f)
# Telegram bot API Token (可在 @botfather 获取，如 10xxx4:AAFcqxxxxgER5uw)
TOKEN = config["TOKEN"]
# WARP 应用内的设备 ID
REFERRER = config["REFERRER"]
# Telegram 用户 ID (给 @getidsbot 发送 /start 获取到的纯数字 ID，如 1434078534)
USER_ID = int(config["USER_ID"])
# 限制其他用户单次刷取次数，如 10，不限制则输入 0
GIFT_LIMIT = int(config["GIFT_LIMIT"])

RUNNING = False


class WarpPlus(object):
    def __init__(self, user_id: int) -> None:
        self._user_id = str(user_id)
        self._config_file = "Config/" + self._user_id + ".json"
        self._config = {}
        self._bot = None
        self._update = None
        self._referrer = None
        self._get_referrer()

    def _get_referrer(self) -> None:
        if os.path.exists(self._config_file):
            with open(self._config_file, "r") as f:
                self._config = json.load(f)
            self._referrer = self._config["REFERRER"]

    def _save_referrer(
        self, user_id: str, username: str or None, first_name: str, referrer: str
    ) -> None:
        self._config["USER_ID"] = user_id
        self._config["USERNAME"] = username
        self._config["FIRST_NAME"] = first_name
        self._config["REFERRER"] = referrer
        with open(self._config_file, "w") as f:
            json.dump(self._config, f)

    def _del_referrer(self) -> bool:
        try:
            os.remove(self._config_file)
            return True
        except FileNotFoundError:
            return False

    def gen_string(self, num: int) -> str:
        c = string.ascii_letters + string.digits
        return "".join(random.choice(c) for _ in range(num))

    def gen_digit(self, num: int) -> str:
        d = string.digits
        return "".join(random.choice(d) for _ in range(num))

    @staticmethod
    def ran_sleep(mu: float = 20.220727, sigma: float = 0.3) -> float:
        return random.gauss(mu, sigma)

    def request_cf(self) -> int or str:
        try:
            install_id = self.gen_string(22)
            body = {
                "fcm_token": "{}:APA91b{}".format(install_id, self.gen_string(134)),
                "install_id": install_id,
                "key": "{}=".format(self.gen_string(43)),
                "locale": "es_ES",
                "referrer": self._referrer,
                "tos": datetime.datetime.now().isoformat()[:-3] + "+02:00",
                "type": "Android",
                "warp_enabled": False,
            }
            data = json.dumps(body).encode("utf8")
            headers = {
                "Accept-Encoding": "gzip",
                "Connection": "Keep-Alive",
                "Content-Type": "application/json; charset=UTF-8",
                "Host": "api.cloudflareclient.com",
                "User-Agent": "okhttp/3.12.1",
            }
            req = urllib.request.Request(
                f"https://api.cloudflareclient.com/v0a{self.gen_digit(3)}/reg",
                data,
                headers,
            )
            with urllib.request.urlopen(req) as response:
                return response.getcode()
        except Exception as e:
            return str(e)

    def run(self, n: float) -> None:
        chat_id = self._update.message.chat_id
        g = 0
        b = 0
        start = time.time()
        while RUNNING:
            result = self.request_cf()
            if result == 200:
                g += 1
                retry = WarpPlus.ran_sleep()
                logging.info(f"[★] {g} GB 流量已添加！")
                self._bot.send_message(
                    chat_id=chat_id,
                    text=f"🍺 {g} GB 流量已添加！",
                )
            else:
                b += 1
                retry = WarpPlus.ran_sleep(22.727153)
                logging.info(f"[-] {result}")
                self._bot.send_message(
                    chat_id=chat_id,
                    text=f"⛔️ {result}",
                )
            if g + b >= n:
                break
            logging.info(f"[*] 等待 {retry} 秒，下一个请求即将发出")
            time.sleep(retry)
        end = time.time()
        self._bot.send_message(
            chat_id=chat_id,
            text="📊 WARP+ 推荐奖励统计\n"
            + f"📟 总次数：{g} 次成功 {b} 次失败\n"
            + f"🎉 成功率：{round(g / (g + b) * 100, 2)}%\n"
            + f"⏳ 总耗时：{round((end - start) / 60, 2)} min",
        )


def start(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    first_name = update.message.from_user.first_name
    name = username if username else first_name
    logging.info(f"[+] {name} ({user_id}) 正在使用 WARP+ 推荐奖励机器人")
    context.bot.send_message(
        chat_id=chat_id,
        text=f"🤖 {name}，欢迎使用 WARP+ 推荐奖励机器人\n"
        + f"你可以使用以下命令来控制机器人\n\n"
        + f"/start - 开始使用\n"
        + f"/plus - (<n>) 💂‍♂️管理员账号添加流量，不输入次数视为 +∞\n"
        + f"/bind - <referrer> 绑定账号\n"
        + f"/unbind - 解除绑定\n"
        + f"/gift - (<n>) 获取流量，不输入次数视为 +∞\n"
        + f"/stop - 💂‍♂️管理员停止运行中的任务\n",
    )


def plus(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    if user_id != USER_ID:
        name = update.message.from_user.username
        if not name:
            name = update.message.from_user.first_name
        logging.error(f"[\] {name}({user_id}) 正在使用该命令，但 /plus 只允许管理员使用")
        return context.bot.send_message(
            chat_id=chat_id,
            text="🚫 /plus 只允许管理员使用",
        )
    global RUNNING
    if RUNNING == True:
        logging.error("[\] 请先 /stop 停止正在运行的任务！")
        return context.bot.send_message(
            chat_id=chat_id,
            text="🚫 请先 /stop 停止正在运行的任务！",
        )
    n = "".join(context.args)
    if not n:
        n = float("inf")
        logging.warning("[!] 未输入数字，将进行无限次请求")
        context.bot.send_message(
            chat_id=chat_id,
            text="🛸 未输入数字，将进行无限次请求",
        )
    elif not n.isdigit() or n == "0":
        logging.error("[×] 请输入一个正整数！")
        return context.bot.send_message(
            chat_id=chat_id,
            text="❌ 请输入一个正整数！",
        )
    else:
        n = int(n)
    task = WarpPlus(user_id)
    task._bot = context.bot
    task._update = update
    task._referrer = REFERRER
    RUNNING = True
    task.run(n)
    RUNNING = False


def bind(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    first_name = update.message.from_user.first_name
    name = username if username else first_name
    chat_type = update.message.chat.type
    if chat_type != "private":
        logging.error(f"[\] {name}({user_id}) 正在使用该命令，但 /bind 只允许私聊使用")
        return context.bot.send_message(
            chat_id=chat_id,
            text="🚫 /bind 只允许私聊使用",
        )
    referrer = "".join(context.args)
    if not re.match(r"^[a-z0-9-]{36}$", referrer):
        logging.error("[×] 请输入一个正确的 referrer！")
        return context.bot.send_message(
            chat_id=chat_id,
            text="❌ 请输入一个正确的 referrer！",
        )
    task = WarpPlus(user_id)
    task._save_referrer(user_id, username, first_name, referrer)
    logging.info(f"[√] {name}({user_id}) 绑定成功！")
    context.bot.send_message(
        chat_id=chat_id,
        text=f"🔗 {name}({user_id}) 绑定成功！",
    )


def unbind(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    first_name = update.message.from_user.first_name
    name = username if username else first_name
    task = WarpPlus(user_id)
    if task._del_referrer():
        logging.info(f"[√] {name}({user_id}) 解绑成功！")
        context.bot.send_message(
            chat_id=chat_id,
            text=f"🔓 {name}({user_id}) 解绑成功！",
        )
    else:
        logging.warning(f"[!] {name}({user_id}) 无须解绑！")
        context.bot.send_message(
            chat_id=chat_id,
            text=f"👻 {name}({user_id}) 无须解绑！",
        )


def gift(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    global RUNNING
    if RUNNING == True:
        logging.error("[\] 请先 /stop 停止正在运行的任务！")
        return context.bot.send_message(
            chat_id=chat_id,
            text="🚫 请先 /stop 停止正在运行的任务！",
        )
    user_id = update.message.from_user.id
    task = WarpPlus(user_id)
    if not task._referrer:
        logging.error("[\] 请先私聊使用 /bind 绑定 WARP 应用内的设备 ID！")
        return context.bot.send_message(
            chat_id=chat_id,
            text="🔑 请先私聊使用 /bind 绑定 WARP 应用内的设备 ID！",
        )
    task._bot = context.bot
    task._update = update
    n = "".join(context.args)
    global GIFT_LIMIT
    if not n:
        if GIFT_LIMIT == 0:
            n = float("inf")
            logging.warning("[!] 未输入数字，将进行无限次请求")
            context.bot.send_message(
                chat_id=chat_id,
                text="🛸 未输入数字，将进行无限次请求",
            )
        else:
            n = random.randint(1, GIFT_LIMIT)
            logging.warning(f"[!] 未输入数字，最大限制为 {GIFT_LIMIT} 次，将进行 {n} 次请求")
            context.bot.send_message(
                chat_id=chat_id,
                text=f"🎲 未输入数字，最大限制为 {GIFT_LIMIT} 次，将进行 {n} 次请求",
            )
    elif not n.isdigit() or n == "0":
        logging.error("[×] 请输入一个正整数！")
        return context.bot.send_message(
            chat_id=chat_id,
            text="❌ 请输入一个正整数！",
        )
    else:
        n = int(n)
        if GIFT_LIMIT != 0 and n > GIFT_LIMIT:
            logging.error(f"[×] 管理员开启了最大限制，请输入一个小于等于 {GIFT_LIMIT} 的正整数！")
            return context.bot.send_message(
                chat_id=chat_id,
                text=f"🛡 管理员开启了最大限制，请输入一个小于等于 {GIFT_LIMIT} 的正整数！",
            )
    RUNNING = True
    task.run(n)
    RUNNING = False


def stop(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    if user_id != USER_ID:
        name = update.message.from_user.username
        if not name:
            name = update.message.from_user.first_name
        logging.error(f"[\] {name}({user_id}) 正在使用该命令，但 /stop 只允许管理员使用")
        return context.bot.send_message(
            chat_id=chat_id,
            text="🚫 /stop 只允许管理员使用",
        )
    global RUNNING
    if RUNNING == True:
        logging.info("[-] WARP+ 推荐奖励任务终止")
        context.bot.send_message(chat_id=chat_id, text="🛑 WARP+ 推荐奖励任务终止")
        RUNNING = False
    else:
        logging.warning("[\] 没有正在运行的任务！")
        context.bot.send_message(chat_id=chat_id, text="⚠️ 没有正在运行的任务！")


def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("plus", plus, run_async=True))
    dp.add_handler(CommandHandler("bind", bind))
    dp.add_handler(CommandHandler("unbind", unbind))
    dp.add_handler(CommandHandler("gift", gift, run_async=True))
    dp.add_handler(CommandHandler("stop", stop))
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
