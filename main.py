#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import sys
from lxml import etree
from lxml import *
import lxml.html
import lxml.html as H
import time
import datetime
import json
import pytz
from generic import *
from threading import Thread
import plugin

danmaku_lock = False
bilimsg_lock = False

def sendReply(source, texts):
    if source["from"] == "bili-danmaku":
        for text in texts:
            sendDanmaku(text)
            time.sleep(1)
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
    bilimsg_lock = False
    if resp["code"] != 0:
        printlog("ERROR", "Failed to send bilibili private message to UID " + str(uid) + ": " + text)
        return False
    printlog("INFO", "Sucessfully sent bilibili private message to UID " + str(uid) + ": " + text)
    return True

def sendDanmaku(text):
    global danmaku_lock
    while danmaku_lock:
        time.sleep(1)
    if isinstance(text, str):
        msg = unicode(text, 'utf-8')
    else:
        msg = text
    if len(msg) > 20:
        count = 1
        for i in range(0, len(text), 20):
            sendDanmaku(text[i:i+20])
        return
    danmaku_lock = True
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
    danmaku_lock = False

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
        bilimsg_ack_seqno = response["data"]["ack_seqno"]
        bilimsg_latest_seqno = response["data"]["latest_seqno"]
    url = "https://api.vc.bilibili.com/web_im/v1/web_im/fetch_msg"
    while True:
        resp = requests.post(url, params = {"access_key": getConfig('assist', 'accesskey')}, data={"client_seqno": bilimsg_ack_seqno, "msg_count": 1, "uid": int(getConfig('assist', 'uid'))}, timeout=3).json()
        if resp["code"] != 0:
            printlog("ERROR", "Failed to receive bilibili private message.")
            return False
        if resp["data"]["has_more"]:
            message = resp["data"]["messages"][0]
            source = {"from": "bili-msg", "uid": message["sender_uid"]}
            if message["msg_type"] == 1:
                printlog("INFO", "New bilibili PM from UID " + str(source["uid"]) + " at " + str(message["timestamp"]) + ": " + json.loads(message["content"])["content"])
            from plugin import commandParse
            if message["msg_type"] != 1 or not commandParse(source, json.loads(message["content"])["content"], message["timestamp"]):
                sendReply(source, ["喵，Cathy不是很确定你在讲什么的喵~", "你可能需要去找我的主人 @SerCom_KC 的喵~"])
            bilimsg_ack_seqno += 1
            bilimsg_latest_seqno = resp["data"]["max_seqno"]
        else:
            url = "https://api.vc.bilibili.com/web_im/v1/web_im/read_ack"
            resp = requests.post(url, params = {"access_key": getConfig('assist', 'accesskey')}, timeout=3)
            if resp["code"] != 0:
                printlog("ERROR", "Failed to mark bilibili private message as read.")
                return False
        time.sleep(5)

def checkConfig():
    if getConfig('oauth', 'appkey') == '' or getConfig('oauth', 'appsecret') == '':
        printlog("ERROR", "You must set up OAuth application info in config.ini")
        quit()
    try:
        checkToken('host')
        time.sleep(1)
        checkToken('assist')
    except requests.exceptions.Timeout:
        pass

def onexit():
    printlog("INFO", "Cathy is off.")

if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf-8')
    checkConfig()
    global start_time
    if len(sys.argv) != 1 and sys.argv[1] == 'initStream':
        plugin.initStream(sys.argv[2])
        quit()
    printlog('INFO', 'Cathy is on!')
    atexit.register(onexit)
    start_time = int(time.time())
    from biliws import listenDanmaku
    Thread(target=listenDanmaku).start()
    Thread(target=listenBiliMsg).start()
    try:
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
