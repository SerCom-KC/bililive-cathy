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

now_last_query = ''
next_last_query = ''

def getShow(id):
    id = id.lower()
    if id == 'tawog':
        return "The Amazing World of Gumball"
    elif id == 'cl':
        return "Clarence"
    elif id == 'ttg':
        return "Teen Titans Go!"
    elif id == 'tt':
        return "Teen Titans"
    elif id == 'uni':
        return "Unikitty"
    elif id == 'at':
        return "Adventure Time"
    elif id == 'ben10':
        return "Ben 10"
    elif id == 'wbb':
        return "We Bare Bears"
    elif id == 'okko':
        return "OK K.O.! Let's Be Heroes!"
    else:
        return "ERROR"

def nowOnAir():
    global now_last_query
    global next_last_query
    if now_last_query == '' or int(time.time()) > convertTime(now_last_query['endTime']):
        sendDanmaku(u'稍等一下哦，Cathy去查查放送表的喵~')
        url = "https://tvlistings.zap2it.com/api/grid"
        params = {
            'time': str(int(time.time())),
            'device': 'X',
            'headendId': 'KY16593',
            'timespan': '15',
            'country': 'USA'
        }        
        origlist = requests.get(url, params=params).json()['channels']
        list = False
        for item in origlist:
            if item['callSign'] == 'TOON':
                list = item['events']
                break
        if not list:
            sendDanmaku(u'Cathy也不知道的喵~')
            return
        now_last_query = list[0]
        next_last_query = list[1]
    sendDanmaku(u'正在播出的是：')
    time.sleep(1)
    sendDanmaku(now_last_query['program']['title'])
    time.sleep(1)
    sendDanmaku(u'这集的标题是：')
    time.sleep(1)
    sendDanmaku(now_last_query['program']['episodeTitle'])

def nextOnAir(text):
    global now_last_query
    global next_last_query
    if text.replace(' ','') == '#next':
        timespan = '3'
    else:
        timespan = '12'
        show_name = getShow(text.replace('#next ', ''))
        if show_name == 'ERROR':
            sendDanmaku(u'你输入的命令好像有误的喵~')
            return
    if timespan == '12' or next_last_query == '' or int(time.time()) > convertTime(now_last_query['endTime']):
        sendDanmaku(u'稍等一下哦，Cathy去查查放送表的喵~')
        url = "https://tvlistings.zap2it.com/api/grid"
        params = {
            'time': str(int(time.time())),
            'device': 'X',
            'headendId': 'KY16593',
            'timespan': timespan,
            'country': 'USA'
        }        
        origlist = requests.get(url, params=params).json()['channels']
        list = False
        for item in origlist:
            if item['callSign'] == 'TOON':
                list = item['events']
                break
        if not list:
            sendDanmaku(u'Cathy也不知道的喵~')
            return
        now_last_query = list[0]
        next_last_query = list[1]
    if timespan == '3':
        sendDanmaku(u'接下来播出的是：')
        time.sleep(1)
        sendDanmaku(next_last_query['program']['title'])
        time.sleep(1)
        sendDanmaku(u'这集的标题是：')
        time.sleep(1)
        sendDanmaku(next_last_query['program']['episodeTitle'])
    elif timespan == '12':
        for item in list:
            if item['program']['title'] == show_name:
                sendDanmaku(u'下一次播出时间（北京时间）：')
                time.sleep(1)
                sendDanmaku(datetime.datetime.fromtimestamp(convertTime(item['endTime'])).strftime('%m月%d日%H:%M'))
                time.sleep(1)
                sendDanmaku(u'这集的标题是：')
                time.sleep(1)
                sendDanmaku(item['program']['episodeTitle'])
                return
        sendDanmaku(u'12小时内没有发现放送的喵~')

def newOnAir(text):
    if text.replace(' ','') != '#new':
        show_name = getShow(text.replace('#new ', ''))
        if show_name == 'ERROR':
            sendDanmaku(u'你输入的命令好像有误的喵~')
            return
    url = "https://catting.net/nep.json"
    list = requests.get(url).json()
    for item in list:
        if item[8] == "Cartoon Network" or item[8] == "Adult Swim":
            if text.replace(' ','') != '#new' and item[9] == show_name:
                sendDanmaku(u'下一次首播时间（北京时间）：')
                time.sleep(1)
                sendDanmaku(time.strftime('%m月%d日%H:%M', time.localtime(int(item[0]))))
                time.sleep(1)
                sendDanmaku(u'这集的标题是：')
                time.sleep(1)
                sendDanmaku(item[10])
                time.sleep(1)
                return
            elif text.replace(' ','') == '#new':
                sendDanmaku(u'即将在' + item[8] + u'首播')
                time.sleep(1)
                sendDanmaku(item[9])
                time.sleep(1)
                sendDanmaku(u'播出时间（北京时间）：')
                time.sleep(1)
                sendDanmaku(time.strftime('%m月%d日%H:%M', time.localtime(int(item[0]))))
                time.sleep(1)
                sendDanmaku(u'这集的标题是：')
                time.sleep(1)
                sendDanmaku(item[10])
                time.sleep(1)
                return
    if show_name:
        sendDanmaku(u'两周内没有发现首播的喵~')
    else:
        sendDanmaku(u'Cathy也不知道的喵~')

def danmakuIdentify(uid, username, text):
    if str(uid) == '277336328':
        return
    printlog("INFO", "New danmaku from " + username + ": " + text)
    if str(uid) == BILI_UID:
        if text == '#status':
            sendDanmaku(u'Cathy在的喵~')
    if text == '#now':
        nowOnAir()
    elif text.find('#new') == 0:
        newOnAir(text)
    elif text.find('#next') == 0:
        nextOnAir(text)

def sendDanmaku(text):
    global danmaku_lock
    bili_cookie = ASSIST_COOKIE
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
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cookie': bili_cookie
        }
        data = {
            'roomid': bili_roomid,
            'color': '16777215',
            'fontsize': '25',
            'mode': '1',
            'msg': msg,
        }
        response = requests.post(url, headers=headers, data=data).json()
        if response["code"] == 0:
            printlog("INFO", "Successfully sent danmaku: " + text)
        else:
            printlog("ERROR", "Failed to send danmaku: " + text)
    except Exception as e:
        printlog("ERROR", "An unexpected error occurred while sending danmaku " + text)
        print(e)
    time.sleep(1.5)
    danmaku_lock = False

def isLiving():
    printlog("INFO", "Checking if live stream is down...")
    url = 'https://live.bilibili.com/bili/isliving/' + BILI_UID
    live_statusdata = json.loads(requests.get(url).content.replace('(', '').replace(');', ''))["data"]
    if live_statusdata == "":
        return False
    else:
        return True

def restartStream():
    printlog("INFO", "Attempting to restart live stream...")
    printlog("INFO", "Killing ffmpeg...")
    os.system('killall ffmpeg')

def startLive():
    bili_cookie = OWNER_COOKIE
    printlog("INFO", "Attempting to turn the switch on...")
    url = 'https://api.live.bilibili.com/room/v1/Room/startLive'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Cookie': bili_cookie
    }
    data = {
        'room_id': bili_roomid,
        'platform': 'pc',
        'area_v2': CATEGORY_ID # live stream category
    }
    response = requests.post(url, headers=headers, data=data).json()
    if response["code"] != 0:
        printlog("ERROR", "Failed to turn the switch. Has the cookie expired? Anyway, I'm quitting.")
        quit()
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
    if BILI_UID == '':
        printlog("ERROR", "You must set up BILI_UID in config.py.")
        quit()
    elif OWNER_COOKIE == '':
        printlog("ERROR", "You must set up OWNER_COOKIE in config.py.")
        quit()
    elif CATEGORY_ID == '':
        printlog("ERROR", "You must set up CATEGORY_ID in config.py.")
        quit()
    elif ASSIST_COOKIE == '':
        printlog("WARNING", "You must set up ASSIST_COOKIE in config.py.")
        quit()

if __name__ == '__main__':
    checkConfig()
    global start_time
    if len(sys.argv) != 1 and sys.argv[1] == 'initStream':
        plugin.initStream(sys.argv)
        quit()
    printlog('INFO', 'Cathy is on!')
    start_time = int(time.time())
    from biliws import listenDanmaku
    Pool(processes=1).apply_async(listenDanmaku)
    if not isLiving():
        printlog("INFO", "Looks like the live switch is OFF. The time now is " + time.ctime())
        startLive()
        restartStream()
    try:
        while True:
            try:
                time.sleep(1)
            except Exception as e:
                printlog("ERROR", "Unexpected error occurred.")
                print(e)
    except KeyboardInterrupt:
            printlog('INFO', 'Force terminating...')