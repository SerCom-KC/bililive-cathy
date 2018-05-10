#!/usr/bin/env python
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

def sendReply(source, texts):
    if source["from"] == "bili-danmaku":
        Thread(target=sendBatchDanmaku, args=[texts, source["username"]]).start()
    elif source["from"] == "bili-msg":
        sendBiliMsg(source["uid"], '\n'.join(texts))
    else:
        printlog("ERROR", "Invalid sendReply source!")

def sendBiliMsg(uid, text):
    global bilimsg_lock
    while bilimsg_lock:
        time.sleep(1)
    bilimsg_lock = True
    url = "https://api.vc.bilibili.com/web_im/v1/web_im/send_msg"
    resp = bilireq(
               url,
               data = {
                   "msg[sender_uid]": int(getConfig('assist', 'uid')),
                   "msg[receiver_id]": uid,
                   "msg[receiver_type]": 1,
                   "msg[msg_type]": 1,
                   "msg[content]": '{"content":"' + text + '"}',
                   "msg[timestamp]": int(time.time())
               }, cookies=bili_cookie['assist']).json()
    time.sleep(5)
    bilimsg_lock = False
    if resp["code"] != 0:
        printlog("ERROR", "Failed to send bilibili private message to UID " + str(uid) + ": " + text)
        return False
    printlog("INFO", "Sucessfully sent bilibili private message to UID " + str(uid) + ": " + text)
    return True

def sendBatchDanmaku(texts, username):
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

def sendDanmaku(text):
    global danmaku_limit
    if isinstance(text, str):
        msg = unicode(text, 'utf-8')
    else:
        msg = text
    if len(msg) > danmaku_limit:
        count = 1
        for i in range(0, len(text), danmaku_limit):
            sendDanmaku(text[i:i+danmaku_limit])
        return
    try:
        url = "http://api.live.bilibili.com/msg/send"
        params = {
            'access_key': getConfig('assist', 'accesskey')
        }
        data = {
            'roomid': bili_roomid,
            'color': '16777215',
            'fontsize': '25',
            'mode': '1',
            'msg': msg
        }
        response = bilireq(url, params=params, data=data).json()
        if response["code"] != 0:
            printlog("ERROR", "Failed to send danmaku: " + text + ". API says " + response["msg"])
    except Exception as e:
        printlog("ERROR", "An unexpected error occurred while sending danmaku " + text)
        printlog("TRACEBACK", "\n" + traceback.format_exc())
    time.sleep(1.5)

def isLiving():
    printlog("INFO", "Checking if live stream is down...")
    url = 'https://live.bilibili.com/bili/isliving/' + getConfig('host', 'uid')
    live_statusdata = json.loads(requests.get(url, timeout=3).content.replace('(', '').replace(');', ''))["data"]
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
        'room_id': bili_roomid,
        'platform': 'pc_link',
        'area_v2': getConfig('host', 'category')
    }
    response = bilireq(url, data=data).json()
    if response["code"] != 0:
        printlog("ERROR", "Failed to turn on the switch. API says " + response["message"])
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
    url = "https://api.vc.bilibili.com/web_im/v1/web_im/unread_msgs"
    response = requests.post(url, params = {"access_key": getConfig('assist', 'accesskey')}, timeout=3).json()
    if response["code"] != 0:
        printlog("ERROR", "Failed to initialize bilibili private message.")
        return False
    else:
        bilimsg_ack_seqno = response["data"]["latest_seqno"]
        bilimsg_latest_seqno = response["data"]["latest_seqno"]
    while True:
        url = "https://api.vc.bilibili.com/web_im/v1/web_im/fetch_msg"
        response = requests.post(url, params = {"access_key": getConfig('assist', 'accesskey')}, data={"client_seqno": bilimsg_ack_seqno, "msg_count": 1, "uid": int(getConfig('assist', 'uid'))}, timeout=3).json()
        if response["code"] != 0:
            printlog("ERROR", "Failed to receive bilibili private message.")
            return False
        if response["data"]["has_more"]:
            message = response["data"]["messages"][0]
            url = "https://api.live.bilibili.com/user/v2/User/getMultiple"
            response = requests.post(url, params = {"access_key": getConfig('assist', 'accesskey')}, data = {"uids[0]": message["sender_uid"], "attributes[0]": "info"}, timeout=3).json()
            if response["code"] != 0:
                printlog("ERROR", "Failed to get username of bilibili UID " + str(message["sender_uid"]) + ".")
                username = ""
            else:
                username = response["data"][str(message["sender_uid"])]["info"]["uname"]
            source = {"from": "bili-msg", "uid": message["sender_uid"], "username": username}
            if message["msg_type"] == 1:
                printlog("INFO", "New bilibili PM from " + username + " (" + str(source["uid"]) + ") at " + str(message["timestamp"]) + ": " + json.loads(message["content"])["content"])
            from plugin import commandParse
            if message["msg_type"] != 1 or not commandParse(source, json.loads(message["content"])["content"], message["timestamp"]):
                sendReply(source, ["喵，Cathy不是很确定你在讲什么的喵~", "你可能需要去找我的主人 @SerCom_KC 的喵~"])
            bilimsg_ack_seqno += 1
            bilimsg_latest_seqno = response["data"]["max_seqno"]
        else:
            url = "https://api.vc.bilibili.com/web_im/v1/web_im/read_ack"
            response = requests.post(url, params = {"access_key": getConfig('assist', 'accesskey')}, timeout=3).json()
            if response["code"] != 0:
                printlog("ERROR", "Failed to mark bilibili private message as read.")
                return False
        time.sleep(5)

def checkConfig(firstrun=False):
    if getConfig('oauth', 'appkey') == '' or getConfig('oauth', 'appsecret') == '':
        printlog("ERROR", "You must set up OAuth application info in config.ini")
        quit()
    try:
        checkToken('host', firstrun)
        time.sleep(1)
        checkToken('assist', firstrun)
    except requests.exceptions.Timeout:
        pass

def onexit():
    printlog("INFO", "Cathy is off.")

if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf-8')
    checkConfig(True)
    url = "https://api.live.bilibili.com/api/player"
    response = requests.get(url, params = {"access_key": getConfig('assist', 'accesskey'), "id": "cid:" + bili_roomid}, timeout=3).text
    global danmaku_limit
    danmaku_limit = int(re.search(r'<msg_length>[0-9]*</msg_length>', response).group(0).replace('<msg_length>', '').replace('', '</msg_length>'))
    global start_time
    if len(sys.argv) != 1 and sys.argv[1] == 'initStream':
        plugin.initStream(sys.argv[2])
        quit()
    printlog('INFO', 'Cathy is on!')
    atexit.register(onexit)
    start_time = int(time.time())
    from biliws import listenDanmaku
    try:
        Thread(target=listenDanmaku).start()
        Thread(target=listenBiliMsg).start()
        while True:
            try:
                plugin.getSchedule()
                checkConfig()
                time.sleep(5)
            except Exception as e:
                printlog("ERROR", "Unexpected error occurred.")
                printlog("TRACEBACK", "\n" + traceback.format_exc())
    except KeyboardInterrupt:
        printlog('INFO', 'Force terminating...')
        onexit()
        os._exit(0)
