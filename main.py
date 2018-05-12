#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import time
import datetime
import json
import pytz
from generic import *
from threading import Thread
import plugin

danmaku_lock = False
bilimsg_lock = False
danmaku_limit = 20

def sendReply(source, responses, type="text"):
    if source["from"] == "bili-danmaku":
        Thread(target=sendBatchDanmaku, args=[responses, source["username"]]).start()
    elif source["from"] == "bili-msg":
        sendBiliMsg(source, r'\n'.join(responses))
    elif source["from"] == "telegram-private":
        sendTelegramMsg(source, '\n'.join(responses))
    elif source["from"] == "telegram-inlinequery":
        if type == "telegram-inlinequeryresult":
            results = responses
        else:
            results = [{"type": "article", "id": str(int(source["id"]) + int(time.time())), "title": "在当前对话中发送结果", "input_message_content": {"message_text": '\n'.join(responses)}, "description": "查询结果将会对当前会话中的所有参与者可见的喵~"}]
        answerTelegramInlineQuery(source, results)
    else:
        printlog("ERROR", "Invalid sendReply source!")

def sendBusy(source, text="稍等一下的喵~"):
    if source["from"] == "bili-danmaku" or source["from"] == "bili-msg":
        sendReply(source, [text])
    elif source["from"] == "telegram-private":
        url = TELEGRAM_API + "/bot" + getConfig('telegram', 'token') + "/sendChatAction"
        requests.get(url, params = {"chat_id": source["chat"]["id"], "action": "typing"}, timeout=1)
    elif source["from"] == "telegram-inlinequery":
        pass
    else:
        printlog("ERROR", "Invalid sendReply source!")

def sendBiliMsg(source, text):
    global bilimsg_lock
    while bilimsg_lock:
        time.sleep(1)
    bilimsg_lock = True
    url = "https://api.vc.bilibili.com/web_im/v1/web_im/send_msg"
    resp = bilireq(
               url,
               data = {
                   "msg[sender_uid]": int(getConfig('assist', 'uid')),
                   "msg[receiver_id]": source["uid"],
                   "msg[receiver_type]": 1,
                   "msg[msg_type]": 1,
                   "msg[content]": '{"content":"' + text + '"}',
                   "msg[timestamp]": int(time.time())
               }, cookies=getBiliCookie('assist')).json()
    time.sleep(1)
    bilimsg_lock = False
    if resp["code"] != 0:
        printlog("ERROR", "Failed to send bilibili private message to " + source["username"] + " (" + str(source["uid"]) + "): " + text + ". API says " + resp["msg"])
        return False
    printlog("INFO", "Sucessfully sent bilibili private message to " + source["username"] + " (" + str(source["uid"]) + "): " + text)
    return True

def sendTelegramMsg(source, text):
    url = TELEGRAM_API + "/bot" + getConfig('telegram', 'token') + "/sendMessage"
    response = requests.get(url, params = {"chat_id": source["chat"]["id"], "text": text, "reply_to_message_id": source["message_id"]}, timeout=3).json()
    if not response["ok"]:
        printlog("ERROR", "Failed to send Telegram private message to " + source["user"]["first_name"] + " (" + str(source["user"]["id"]) + "): " + text + ". API says " + response["description"])
        return False
    printlog("INFO", "Sucessfully sent Telegram private message to " + source["user"]["first_name"] + " (" + str(source["user"]["id"]) + "): " + text)
    return True

def answerTelegramInlineQuery(source, results):
    #printlog("INFO", "Answering Telegram inline query from " + source["user"]["first_name"] + " (" + str(source["user"]["id"]) + "): " + repr(results))
    url = TELEGRAM_API + "/bot" + getConfig('telegram', 'token') + "/answerInlineQuery"
    response = requests.get(url, params = {"inline_query_id": source["id"], "results": json.dumps(results), "cache_time": 0}, timeout=3).json()
    if not response["ok"]:
        printlog("ERROR", "Failed to answer Telegram inline query from " + source["user"]["first_name"] + " (" + str(source["user"]["id"]) + "). API says " + response["description"])
        return False
    #printlog("INFO", "Sucessfully answered Telegram inline query from " + source["user"]["first_name"] + " (" + str(source["user"]["id"]) + ").")
    return True

def sendBatchDanmaku(texts, username):
    try:
        global danmaku_lock
        while danmaku_lock:
            if texts[0].find("@") != 0:
                texts.insert(0, "@" + username)
            time.sleep(1)
        danmaku_lock = True
        for text in texts:
            sendDanmaku(text)
            time.sleep(1)
        danmaku_lock = False
    except Exception:
        printlog("ERROR", "An unexpected error occurred while sending danmakus: " + '\n'.join(texts))
        printlog("TRACEBACK", "\n" + traceback.format_exc())

def sendDanmaku(text):
    global danmaku_limit
    msg = text
    if len(msg) > danmaku_limit:
        count = 1
        for i in range(0, len(text), danmaku_limit):
            sendDanmaku(text[i:i+danmaku_limit])
        return
    url = "http://api.live.bilibili.com/msg/send"
    params = {
        'access_key': getConfig('assist', 'accesskey')
    }
    data = {
        'roomid': getConfig('host', 'roomid'),
        'color': '16777215',
        'fontsize': '25',
        'mode': '1',
        'msg': msg
    }
    response = bilireq(url, params=params, data=data).json()
    if response["code"] != 0:
        printlog("ERROR", "Failed to send danmaku: " + text + ". API says " + response["msg"])
    time.sleep(1.5)

def isLiving():
    printlog("INFO", "Checking if live stream is down...")
    url = 'https://live.bilibili.com/bili/isliving/' + getConfig('host', 'uid')
    response = requests.get(url, timeout=3).text.replace('(', '').replace(');', '')
    live_statusdata = json.loads(response)["data"]
    if live_statusdata == "":
        return False
    else:
        printlog("INFO", "Live stream switch is ON.")
        return True

def restartStream():
    printlog("INFO", "Attempting to restart live stream...")
    plugin.initStream(plugin.getChannel(), False)
    printlog("INFO", "The live stream should be back online now.")

def startLive():
    printlog("INFO", "Attempting to turn the switch on...")
    url = 'https://api.live.bilibili.com/room/v1/Room/startLive'
    data = {
        'access_key': getConfig('host', 'accesskey'),
        'room_id': getConfig('host', 'roomid'),
        'platform': 'pc_link',
        'area_v2': getConfig('host', 'category')
    }
    response = bilireq(url, data=data).json()
    if response["code"] != 0:
        printlog("ERROR", "Failed to turn on the switch. API says " + response["msg"])
        raise SystemExit
    elif response["data"]["change"] == 0:
        printlog("ERROR", "Looks like the switch is on already.")
        return -1
    else:
        printlog("INFO", "Live switch is now ON. The time now is " + time.ctime())
        #addr = response["data"]["rtmp"]["addr"]
        #code = response["data"]["rtmp"]["code"]
        #new_link = requests.get(response["data"]["rtmp"]["new_link"], timeout=3).json()["data"]["url"]
        return 0

def listenBiliMsg():
    from plugin import commandParse
    url = "https://api.vc.bilibili.com/web_im/v1/web_im/unread_msgs"
    response = requests.post(url, params = {"access_key": getConfig('assist', 'accesskey')}, timeout=3).json()
    if response["code"] != 0:
        printlog("ERROR", "Failed to initialize bilibili private message. API says " + response["msg"])
        raise SystemExit
    else:
        seqno = response["data"]["latest_seqno"]
    s = requests.Session()
    while True:
        try:
            url = "https://api.vc.bilibili.com/web_im/v1/web_im/fetch_msg"
            response = s.post(url, params = {"access_key": getConfig('assist', 'accesskey')}, data={"client_seqno": seqno, "msg_count": 100, "uid": int(getConfig('assist', 'uid'))}, timeout=6).json()
            if response["code"] != 0:
                printlog("ERROR", "Failed to receive bilibili private message. API says " + response["msg"])
            elif "messages" in response["data"]:
                seqno = response["data"]["max_seqno"]
                for message in response["data"]["messages"]:
                    url = "https://api.vc.bilibili.com/account/v1/user/infos"
                    response = s.get(url, params = {"access_key": getConfig('assist', 'accesskey'), "uids": message["sender_uid"]}, timeout=3).json()
                    if response["code"] != 0:
                        printlog("ERROR", "Failed to get username of bilibili UID " + str(message["sender_uid"]) + ". API says " + response["msg"])
                        username = ""
                    else:
                        username = response["data"][0]["uname"]
                    source = {"from": "bili-msg", "uid": message["sender_uid"], "username": username}
                    if message["msg_type"] == 1:
                        printlog("INFO", "New bilibili PM from " + username + " (" + str(source["uid"]) + ") at " + str(message["timestamp"]) + ": " + json.loads(message["content"])["content"])
                    if message["msg_type"] != 1 or not commandParse(source, json.loads(message["content"])["content"]):
                        sendReply(source, ["喵，Cathy不是很确定你在讲什么的喵~", "你可能需要去找我的主人 @SerCom_KC，或者发送 #help 获取命令列表的喵~"])
            time.sleep(1)
        except Exception:
            printlog("ERROR", "An unexpected error occurred while processing bilibili PMs.")
            printlog("TRACEBACK", "\n" + traceback.format_exc())

def listenTelegramUpdate():
    from plugin import commandParse
    s = requests.Session()
    url = TELEGRAM_API + "/bot" + getConfig('telegram', 'token') + "/getMe"
    bot_username = s.get(url, timeout=3).json()["result"]["username"]
    url = TELEGRAM_API + "/bot" + getConfig('telegram', 'token') + "/getUpdates"
    offset = None
    response = s.get(url, params = {"offset": -1, "limit": 1, "allowed_updates": ["message", "inline_query"]}, timeout=3).json()
    if not response["ok"]:
        printlog("ERROR", "Failed to initialize Telegram update. API says " + response["description"])
        raise SystemExit
    elif response["result"] != []:
        offset = response["result"][0]["update_id"] + 1
    while True:
        try:
            url = TELEGRAM_API + "/bot" + getConfig('telegram', 'token') + "/getUpdates"
            response = s.get(url, params = {"offset": offset, "limit": 100, "timeout": 6, "allowed_updates": ["message", "inline_query"]}, timeout=10).json()
            if not response["ok"]:
                printlog("ERROR", "Failed to retrive Telegram updates. API says " + response["description"])
            else:
                for update in response["result"]:
                    offset = update["update_id"] + 1
                    if "message" in update:
                        message = update["message"]
                        if message["chat"]["type"] == "private":
                            source = {"from": "telegram-private", "user": message["from"], "chat": message["chat"], "message_id": message["message_id"]}
                            if "text" in message:
                                printlog("INFO", "New Telegram PM from " + message["from"]["first_name"] + " (" + str(message["from"]["id"]) + ") at " + str(message["date"]) + ": " + message["text"])
                                text = message["text"]
                                text = text.replace('@' + bot_username, '', 1) if re.match(r'/\w*@' + bot_username, text) else text
                                text = text.replace('/', '#', 1) if text[0] == '/' else text
                            if not "text" in message or not commandParse(source, text):
                                sendReply(source, ["喵，Cathy不是很确定你在讲什么的喵~", "你可能需要去找我的主人 @szescxz，或者发送 /help 获取命令列表的喵~"])
                    elif "inline_query" in update:
                        query = update["inline_query"]
                        source = {"from": "telegram-inlinequery", "user": query["from"], "id": query["id"]}
                        #printlog("INFO", "New Telegram inline query from " + query["from"]["first_name"] + " (" + str(query["from"]["id"]) + "): " + query["query"])
                        if not commandParse(source, query["query"]):
                            results = [{"type": "article", "id": str(int(source["id"]) + int(time.time())), "title": "请输入以#开头的命令喵~", "input_message_content": {"message_text": "喵，Cathy不是很确定你在问什么的喵~\n你可能需要去找我的主人 @szescxz，或者输入 @" + bot_username + " #help 获取命令列表的喵~"}, "description": "输入 #help 可以获取命令列表的喵~"}]
                            sendReply(source, results, "telegram-inlinequeryresult")
            time.sleep(1)
        except Exception:
            printlog("ERROR", "An unexpected error occurred while processing Telegram updates.")
            printlog("TRACEBACK", "\n" + traceback.format_exc())

def checkConfig(firstrun=False):
    global danmaku_limit
    if sys.stdout.encoding.lower() != 'utf-8':
        printlog("ERROR", "Looks like the encoding of stdout is not UTF-8. Try adding PYTHONIOENCODING=utf-8 to your environment variables first.")
        raise SystemExit
    if getConfig('oauth', 'appkey') == '' or getConfig('oauth', 'appsecret') == '':
        printlog("ERROR", "You must set up OAuth application info in config.ini")
        raise SystemExit
    checkToken('host', firstrun)
    time.sleep(1)
    checkToken('assist', firstrun)
    if firstrun:
        url = "https://api.live.bilibili.com/api/player"
        response = requests.get(url, params = {"access_key": getConfig('assist', 'accesskey'), "id": "cid:" + getConfig('host', 'roomid')}, timeout=3).text
        danmaku_limit = int(re.search(r'<msg_length>[0-9]*</msg_length>', response).group(0).replace('<msg_length>', '').replace('</msg_length>', ''))
        if getConfig('telegram', 'token') != "":
            url = TELEGRAM_API + "/bot" + getConfig('telegram', 'token') + "/getMe"
            if not requests.get(url, timeout=3).json()["ok"]:
                printlog("ERROR", "Your Telegram bot token seems invalid. Please check your config.ini")
                raise SystemExit

def onexit():
    printlog("INFO", "Cathy is off.")

def main():
    try:
        checkConfig(True)
        global start_time
        if len(sys.argv) != 1 and sys.argv[1] == 'initStream':
            plugin.initStream(sys.argv[2])
            quit()
        printlog('INFO', 'Cathy is on!')
        atexit.register(onexit)
        start_time = int(time.time())
        from biliws import listenDanmaku
        Thread(target=listenDanmaku).start()
        if getConfig('assist', 'pm') == "1":
            Thread(target=listenBiliMsg).start()
        if getConfig('telegram', 'token') != "" and getConfig('telegram', 'pm') == "1":
            Thread(target=listenTelegramUpdate).start()
        while True:
            try:
                plugin.getSchedule()
                checkConfig()
                time.sleep(5)
            except Exception:
                printlog("ERROR", "Unexpected error occurred.")
                printlog("TRACEBACK", "\n" + traceback.format_exc())
    except KeyboardInterrupt:
        printlog('INFO', 'Force terminating...')
        onexit()
        os._exit(0)
    except Exception:
        printlog("ERROR", "Unexpected error occurred.")
        printlog("TRACEBACK", "\n" + traceback.format_exc())

if __name__ == "__main__":
    main()
