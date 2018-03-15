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
from multiprocessing import Pool
import plugin

danmaku_lock = False

def danmakuIdentify(uid, username, text):
    if str(uid) == getConfig('assist', 'uid'): # don't process self
        return
    printlog("INFO", "New danmaku from " + username + " (" + str(uid) + "): " + text)
    if str(uid) == getConfig('host', 'uid'):
        if text == '#status':
            sendDanmaku(u'Cathy在的喵~')
    if text == '#now':
        plugin.nowOnAir()
        #sendDanmaku(u'呜，Cathy的时间表被KC没收了~')
    elif text.find('#new') == 0:
        plugin.newOnAir(text)
    elif text.find('#next') == 0:
        plugin.nextOnAir(text)
        #sendDanmaku(u'呜，Cathy的时间表被KC没收了~')
    elif text.find(u'字幕') != -1:
        sendDanmaku(u'本直播间为无字幕生肉放送，看下简介啊喵！')

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
            'msg': msg,
        }
        response = bilireq(url, params=params, data=data).json()
        if response["code"] == 0:
            printlog("INFO", "Successfully sent danmaku: " + text)
        else:
            printlog("ERROR", "Failed to send danmaku: " + text + ". API says " + response["msg"])
    except Exception as e:
        printlog("ERROR", "An unexpected error occurred while sending danmaku " + text)
        print(e)
    time.sleep(1.5)
    danmaku_lock = False

def isLiving():
    printlog("INFO", "Checking if live stream is down...")
    url = 'https://live.bilibili.com/bili/isliving/' + getConfig('host', 'uid')
    live_statusdata = json.loads(requests.get(url).content.replace('(', '').replace(');', ''))["data"]
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
        #quit() # not working for some reason
    elif response["data"]["change"] == 0:
        printlog("ERROR", "Looks like the switch is on already.")
        return -1
    else:
        printlog("INFO", "Live switch is now ON. The time now is " + time.ctime())
        #addr = response["data"]["rtmp"]["addr"]
        #code = response["data"]["rtmp"]["code"]
        #new_link = requests.get(response["data"]["rtmp"]["new_link"]).json()["data"]["url"]
        return 0

def checkConfig():
    if getConfig('oauth', 'appkey') == '' or getConfig('oauth', 'appsecret') == '':
        printlog("ERROR", "You must set up OAuth application info in config.ini")
        quit()
    checkToken('host')
    checkToken('assist')

if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf-8')
    checkConfig()
    global start_time
    if len(sys.argv) != 1 and sys.argv[1] == 'initStream':
        plugin.initStream(sys.argv[2])
        quit()
    printlog('INFO', 'Cathy is on!')
    start_time = int(time.time())
    from biliws import listenDanmaku
    Pool(processes=1).apply_async(listenDanmaku)
    try:
        while True:
            try:
                time.sleep(1)
            except Exception as e:
                printlog("ERROR", "Unexpected error occurred.")
                print(e)
    except KeyboardInterrupt:
            printlog('INFO', 'Force terminating...')