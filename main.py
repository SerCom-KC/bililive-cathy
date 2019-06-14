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
import random

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
        elif len(responses) == 1:
            results = [{"type": "article", "id": str(int(source["id"]) + int(time.time())), "title": responses[0], "input_message_content": {"message_text": responses[0]}}]
        elif len(responses) == 2:
            results = [{"type": "article", "id": str(int(source["id"]) + int(time.time())), "title": responses[0], "input_message_content": {"message_text": '\n'.join(responses)}, "description": responses[1]}]
        else:
            results = [{"type": "article", "id": str(int(source["id"]) + int(time.time())), "title": "在当前对话中发送结果", "input_message_content": {"message_text": '\n'.join(responses)}, "description": "查询结果将会对当前会话中的所有参与者可见的喵~"}]
        answerTelegramInlineQuery(source, results)
    elif source["from"] == "mastodon":
        sendMastodonStatus(source, '\n'.join(responses))
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
                   "msg[timestamp]": int(time.time()),
                   "msg[dev_id]": source["dev_id"]
               }, cookies=getBiliCookie('assist'), headers={"Referer": "https://message.bilibili.com/"}).json()
    time.sleep(1)
    bilimsg_lock = False
    if resp["code"] != 0:
        printlog("ERROR", "Failed to send bilibili private message to " + source["username"] + " (" + str(source["uid"]) + "): " + text + ". API says " + resp["msg"])
        return False
    printlog("INFO", "Sucessfully sent bilibili private message to " + source["username"] + " (" + str(source["uid"]) + "): " + text)
    return True

def sendTelegramMsg(source, text):
    url = TELEGRAM_API + "/bot" + getConfig('telegram', 'token') + "/sendMessage"
    response = requests.get(url, params = {"chat_id": source["chat"]["id"], "text": text, "reply_to_message_id": source["message_id"]}, timeout=10).json()
    if not response["ok"]:
        printlog("ERROR", "Failed to send Telegram private message to " + source["user"]["first_name"] + " (" + str(source["user"]["id"]) + "): " + text + ". API says " + response["description"])
        return False
    printlog("INFO", "Sucessfully sent Telegram private message to " + source["user"]["first_name"] + " (" + str(source["user"]["id"]) + "): " + text)
    return True

def answerTelegramInlineQuery(source, results):
    #printlog("INFO", "Answering Telegram inline query from " + source["user"]["first_name"] + " (" + str(source["user"]["id"]) + "): " + repr(results))
    url = TELEGRAM_API + "/bot" + getConfig('telegram', 'token') + "/answerInlineQuery"
    response = requests.get(url, params = {"inline_query_id": source["id"], "results": json.dumps(results), "cache_time": 60}, timeout=30).json()
    if not response["ok"]:
        printlog("ERROR", "Failed to answer Telegram inline query from " + source["user"]["first_name"] + " (" + str(source["user"]["id"]) + "). API says " + response["description"])
        return False
    #printlog("INFO", "Sucessfully answered Telegram inline query from " + source["user"]["first_name"] + " (" + str(source["user"]["id"]) + ").")
    return True


def sendMastodonStatus(source, text):
    mastodon_base = 'https://%s' % getConfig('mastodon', 'domain')
    url = mastodon_base + "/api/v1/statuses"
    headers = {
        "Authorization": 'Bearer %s' % getConfig('mastodon', 'accesstoken')
    }
    data = {
        "status": "%s %s" % (source["account"]["acct"], text),
        "in_reply_to_id": source["id"],
        "visibility": source["visibility"],
        "language": "chi"
    }
    response = requests.post(url, data=data, headers=headers, timeout=10).json()
    if "error" in response:
        printlog("ERROR", "Failed to reply Mastodon status to " + source["account"]["display_name"] + " (" + source["account"]["acct"] + "): " + text + ". API says " + response["error"])
        return False
    printlog("INFO", "Sucessfully sent Mastodon status to " + source["account"]["display_name"] + " (" + source["account"]["acct"] + "): " + text)
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
            for retry in range(3):
                if sendDanmaku(text):
                    break
                time.sleep(5)
            time.sleep(1)
        danmaku_lock = False
    except Exception:
        printlog("ERROR", "An unexpected error occurred while sending danmakus: " + '\n'.join(texts))
        printlog("TRACEBACK", "\n" + traceback.format_exc())
        danmaku_lock = False

def sendDanmaku(text):
    global danmaku_limit
    msg = text
    if len(msg) > danmaku_limit:
        count = 1
        for i in range(0, len(text), danmaku_limit):
             if not sendDanmaku(text[i:i+danmaku_limit]):
                 return False
        return True
    url = "https://api.live.bilibili.com/api/sendmsg"
    data = {
        "access_key": getConfig("assist", "accesskey"),
        "cid": getConfig("host", "roomid"),
        "mid": getConfig("assist", "uid"),
        "color": 16777215,
        "fontsize": 25,
        "mode": 1,
        "pool": 1,
        "type": "json",
        "msg": msg,
        "rnd": int(time.time()),
        "playTime": "0.0"
    }
    response = bilireq(url, data=data).json()
    time.sleep(1.5)
    if response["code"] != 0:
        printlog("ERROR", "Failed to send danmaku: " + text + ". API says " + str(response["message"]))
        return False
    else:
        return True

def isLiving():
    printlog("INFO", "Checking if live stream is down...")
    url = 'https://api.live.bilibili.com/room/v1/Room/getRoomInfoOld'
    response = requests.get(url, params={"mid": getConfig('host', 'uid')}, timeout=3).json()
    live_statusdata = response["data"]
    if live_statusdata["liveStatus"] != 1:
        return False
    else:
        printlog("INFO", "Live stream switch is ON.")
        return True


def startLive(argv=None, force=False):
    global startLive_lock
    try:
        if startLive_lock:
            printlog("DEBUG", "startLive_lock is on, cannot proceed.")
            return
    except NameError:
        pass
    try:
        url = "https://api.live.bilibili.com/room/v1/RoomEx/getCutReason"
        data = {
            "access_key": getConfig("host", "accesskey"),
            "room_id": getConfig("host", "roomid")
        }
        resp = bilireq(url, data=data).json()
        printlog("DEBUG", resp)
        if resp["data"] != []:
            printlog("WARNING", "Your livestream was terminated by bilibili.")
            printlog("WARNING", "Please clear the message first.")
            raise SystemExit
    except Exception:
        pass
    startLive_lock = True
    try:
        url = 'https://api.live.bilibili.com/room/v1/Room/startLive'
        data = {
            'access_key': getConfig('host', 'accesskey'),
            'room_id': getConfig('host', 'roomid'),
            'platform': 'pc_link',
            'area_v2': getConfig('host', 'category')
        }
        printlog("DEBUG", "Sending startLive request...")
        response = bilireq(url, data=data).json()
        if response["code"] != 0:
            printlog("ERROR", "Failed to turn on the switch. API says " + response["msg"])
            raise SystemExit
        elif response["data"]["change"] == 0:
            printlog("INFO", "Looks like the live switch is on already.")
            if not force:
                startLive_lock = False
                return -1
        else:
            printlog("INFO", "Live switch is now ON.")
        addr = response["data"]["rtmp"]["addr"]
        code = response["data"]["rtmp"]["code"]
        try:
            new_link = requests.get(response["data"]["rtmp"]["new_link"], timeout=3).json()["data"]["url"]
        except Exception:
            printlog("WARNING", "Failed to retrive IP-based push address, falling back to domain-based.")
            new_link = addr + code
        printlog("INFO", "Attempting to restart live stream...")
        plugin.initStream(argv, notice=True if argv else False, rtmp_push_address=new_link)
        printlog("INFO", "The live stream should be back online now.")
        startLive_lock = False
        return 0
    except Exception:
        printlog("ERROR", "An unexpected error occurred while starting live stream.")
        printlog("TRACEBACK", "\n" + traceback.format_exc())
        startLive_lock = False
        return -1


def listenBiliMsg():
    from plugin import commandParse
    s = requests.Session()
    # ignore all messages prior to script startup
    url = "https://api.vc.bilibili.com/web_im/v1/web_im/unread_msgs" # then let's get current sequence number 
    response = s.post(url, params = {"access_key": getConfig('assist', 'accesskey')}, timeout=3).json()
    if response["code"] != 0:
        printlog("ERROR", "Failed to initialize bilibili private message. API says " + response["msg"])
        raise SystemExit
    # generate device_id
    device_id = "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx"
    for i in range(0, len(device_id)):
        r = int(16 * random.random())
        if device_id[i] == "x":
            device_id = device_id[:i] + format(r, 'x').upper() + device_id[i + 1:]
        elif device_id[i] == "y":
            device_id = device_id[:i] + format(3 & r | 8, 'x').upper() + device_id[i + 1:]
    seqno = response["data"]["latest_seqno"] # we can't use ack_seqno at the moment, because that value can only be updated by mobile app via (maybe?) websocket
    timeout_count = 0
    while True:
        try:
            time.sleep(10)
            url = "https://api.vc.bilibili.com/web_im/v1/web_im/fetch_msg" # get messages, up to 100 at once
            response = s.post(url, params = {"access_key": getConfig('assist', 'accesskey')}, data = {"client_seqno": seqno, "msg_count": 100, "uid": int(getConfig('assist', 'uid')), "dev_id": device_id}, timeout=10).json()
            if response["code"] == -6:
                timeout_count += 1
                continue
            elif response["code"] != 0:
                printlog("ERROR", "Failed to receive bilibili private message [%s]: %s" % (response["code"], response["msg"]))
                continue
            has_more = response["data"]["has_more"]
            if "max_seqno" in response["data"]:
                seqno = response["data"]["max_seqno"]
            if not "messages" in response["data"]:
                continue
            printlog("DEBUG", "New bilibili PMs detected, processing...")
            for message in response["data"]["messages"]:
                if message["sender_uid"] == int(getConfig('assist', 'uid')):
                    continue
                printlog("DEBUG", "Querying additional info about bilibili PM sender...")
                url = "https://api.vc.bilibili.com/account/v1/user/infos" # API does not return uname, so let's make an additional query
                response = s.get(url, params = {"access_key": getConfig('assist', 'accesskey'), "uids": message["sender_uid"]}, timeout=3).json()
                if response["code"] != 0:
                    printlog("ERROR", "Failed to get username of bilibili UID " + str(message["sender_uid"]) + ". API says " + response["msg"])
                    username = ""
                else:
                    username = response["data"][0]["uname"]
                source = {"from": "bili-msg", "uid": message["sender_uid"], "username": username, "dev_id": device_id}
                if message["msg_type"] == 1:
                    printlog("INFO", "New bilibili PM from " + username + " (" + str(source["uid"]) + ") at " + str(message["timestamp"]) + ": " + json.loads(message["content"])["content"])
                if message["msg_type"] != 1 or not commandParse(source, json.loads(message["content"])["content"]):
                    sendReply(source, ["喵，Cathy不是很确定你在讲什么的喵~", "你可能需要去找我的主人 @SerCom_KC，或者发送 #help 获取命令列表的喵~"])
            timeout_count = 0
        except requests.exceptions.ReadTimeout:
            timeout_count += 1
            if timeout_count >= 5:
                printlog("WARNING", "Connection timed out " + str(timeout_count) + " times while processing bilibili PMs.")
        except Exception:
            printlog("ERROR", "An unexpected error occurred while processing bilibili PMs.")
            printlog("TRACEBACK", "\n" + traceback.format_exc())

def listenTelegramUpdate():
    s = requests.Session()
    url = TELEGRAM_API + "/bot" + getConfig('telegram', 'token') + "/getMe"
    bot_username = s.get(url, timeout=3).json()["result"]["username"]
    url = TELEGRAM_API + "/bot" + getConfig('telegram', 'token') + "/getUpdates"
    offset = None
    response = s.get(url, params = {"offset": -1, "limit": 1, "allowed_updates": ["message", "inline_query"]}, timeout=3).json()
    if not response["ok"]:
        printlog("ERROR", "Failed to initialize Telegram update. API says " + response["description"])
        return
    elif response["result"] != []:
        offset = response["result"][0]["update_id"] + 1
    timeout_count = 0
    while True:
        try:
            url = TELEGRAM_API + "/bot" + getConfig('telegram', 'token') + "/getUpdates"
            response = s.get(url, params = {"offset": offset, "limit": 100, "timeout": 2, "allowed_updates": ["message", "inline_query"]}, timeout=5).json()
            if not response["ok"]:
                printlog("ERROR", "Failed to retrive Telegram updates. API says " + response["description"]) 
            else:
                for update in response["result"]:
                    offset = update["update_id"] + 1
                    Thread(target=parseTelegramUpdate, args=[update, bot_username]).start()
            timeout_count = 0
            time.sleep(0.3)
        except requests.exceptions.ReadTimeout:
            timeout_count += 1
            if timeout_count >= 5:
                printlog("WARNING", "Connection timed out " + str(timeout_count) + " times while fetching Telegram updates.")
        except Exception:
            printlog("ERROR", "An unexpected error occurred while fetching Telegram updates.")
            printlog("TRACEBACK", "\n" + traceback.format_exc())


def listenMastodonUpdate():
    s = requests.Session()
    mastodon_base = 'https://%s' % getConfig('mastodon', 'domain')
    headers = {
        "Authorization": 'Bearer %s' % getConfig('mastodon', 'accesstoken')
    }
    url = mastodon_base + "/api/v1/accounts/verify_credentials"
    bot_username = s.get(url, headers=headers, timeout=3).json()["username"]
    url = mastodon_base + "/api/v1/notifications"
    offset = int(getConfig('mastodon', 'offset'))
    timeout_count = 0
    while True:
        try:
            url = mastodon_base + "/api/v1/notifications"
            response = s.get(url, params = {"since_id": offset, "limit": 100, "exclude_types": ["follow", "favourite", "reblog"]}, headers=headers, timeout=5).json()
            if "error" in response:
                printlog("ERROR", "Failed to retrive Mastodon updates. API says " + response["error"])
            else:
                for update in response:
                    offset = int(update["id"]) + 1
                    Thread(target=parseMastodonUpdate, args=[update, bot_username]).start()
                setConfig("mastodon", "offset", offset)
            timeout_count = 0
            time.sleep(5)
        except requests.exceptions.ReadTimeout:
            timeout_count += 1
            if timeout_count >= 5:
                printlog("WARNING", "Connection timed out " + str(timeout_count) + " times while fetching Mastodon updates.")
        except Exception:
            printlog("ERROR", "An unexpected error occurred while fetching Mastodon updates.")
            printlog("TRACEBACK", "\n" + traceback.format_exc())            

def parseTelegramUpdate(update, bot_username):
    from plugin import commandParse
    try:
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
    except Exception:
        printlog("ERROR", "An unexpected error occurred while parsing Telegram updates.")
        printlog("TRACEBACK", "\n" + traceback.format_exc())


def parseMastodonUpdate(update, bot_username):
    from plugin import commandParse
    try:
        if update["type"] == "mention" and "status" in update:
            status = update["status"]
            source = {"from": "mastodon", "account": status["account"], "visibility": status["visibility"], "id": status["id"]}
            import lxml.html
            text = lxml.html.document_fromstring(status["content"]).text_content()
            time = int(pytz.utc.localize(datetime.datetime.strptime(status["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ")).timestamp())
            printlog("INFO", "New Mastodon mention from " + source["account"]["display_name"] + " (" + source["account"]["acct"] + ") at " + str(time) + ": " + text)
            text = text.replace('@' + bot_username, '', 1)
            text = text.lstrip(' ').rstrip(' ')
            text = text.replace('/', '#', 1) if text[0] == '/' else text
            if not commandParse(source, text):
                sendReply(source, ["喵，Cathy不是很确定你在讲什么的喵~", "你可能需要去找我的主人 @SerCom_KC@sckc.stream，或者发送 /help 获取命令列表的喵~"])
    except Exception:
        printlog("ERROR", "An unexpected error occurred while parsing Mastodon updates.")
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


def checkStream():
    flag = False
    try:
        stream_status_code = requests.get(stream_url, timeout=10, stream=True).status_code
        flag = (stream_status_code == 404)
    except Exception:
        flag = True
    if flag:
        fail_count = 0
        while fail_count < 3:
            try:
                url = "https://api.live.bilibili.com/room/v1/Room/playUrl"
                params = {
                    "cid": getConfig("host", "roomid"),
                    "quality": "4",
                    "platform": "web",
                    "otype": "json"
                }
                resp = requests.get(url, params=params, timeout=10).json()
                if resp["code"] == 10001:
                    fail_count += 1
                    continue
                elif resp["code"] != 0:
                    printlog("DEBUG", resp)
                    fail_count += 1
                    continue
                stream_url = resp["data"]["durl"][0]["url"]
                stream_status_code = requests.get(stream_url, timeout=10, stream=True).status_code
                break
            except requests.exceptions.ConnectionError:
                fail_count += 1
                continue
            except requests.exceptions.ReadTimeout:
                fail_count += 1
                continue
        if fail_count >= 3:
            printlog("WARNING", "Connection error occurred 3 times while checking bilibili live stream.")
            return True
    if stream_status_code == 404:
        return False
    return True

def onexit():
    printlog("INFO", "Cathy is off.")

def main():
    for retries in range(3): # make sure initStream will run even if unexpected error occurs
        try:
            checkConfig(True)
            break
        except Exception:
            printlog("ERROR", "Unexpected error occurred during initialization.")
            printlog("TRACEBACK", "\n" + traceback.format_exc())
    try:
        if len(sys.argv) != 1 and sys.argv[1] == 'initStream':
            startLive(sys.argv[2], force=True)
            raise SystemExit
        setConfig('extras', 'start_time', int(time.time()))
        printlog('INFO', 'Cathy is on!')
        atexit.register(onexit)
        from biliws import listenDanmaku
        Thread(target=listenDanmaku).start()
        if getConfig('assist', 'pm') == "1":
            Thread(target=listenBiliMsg).start()
        if getConfig('telegram', 'token') != "" and getConfig('telegram', 'pm') == "1":
            Thread(target=listenTelegramUpdate).start()
        if getConfig('mastodon', 'domain') != "" and getConfig('mastodon', 'accesstoken') != "":
            Thread(target=listenMastodonUpdate).start()
        plugin.getSchedule(forceupdate=True)
        streamoff_count = 0
        while True:
            try:
                plugin.getSchedule()
                checkConfig()
                if not checkStream():
                    streamoff_count += 1
                else:
                    streamoff_count = 0
                if streamoff_count >= 3:
                    startLive(force=True)
                    streamoff_count = 0
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
