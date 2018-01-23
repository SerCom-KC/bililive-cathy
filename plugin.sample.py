# -*- coding: utf-8 -*-
from generic import *
import os
import time

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
    from main import sendDanmaku
    global now_last_query
    global next_last_query
    if now_last_query == '' or int(time.time()) > convertTime(now_last_query['endTime']):
        sendDanmaku(u'稍等一下哦，Cathy去查查放送表的喵~')
        url = "https://tvlistings.zap2it.com/api/grid"
        params = {
            'time': str(int(time.time())),
            'device': 'X',
            'headendId': 'KY16593',
            'timespan': '3',
            'country': 'USA'
        }
        origlist = requests.get(url, params=params).json()['channels']
        list = False
        for item in origlist:
            if item['callSign'] == 'TOON' and not isTBS():
                list = item['events']
                break
            elif item['callSign'] == 'TBS' and isTBS():
                list = item['events']
                break
        if not list:
            sendDanmaku(u'Cathy也不知道的喵~')
            return
        now_last_query = list[0]
        if not isTBS(convertTime(list[1]['startTime'])):
            next_last_query = list[1]
    sendDanmaku(u'正在播出的是：')
    time.sleep(1)
    sendDanmaku(now_last_query['program']['title'])
    if now_last_query['program']['episodeTitle'] != None:
        time.sleep(1)
        sendDanmaku(u'这集的标题是：')
        time.sleep(1)
        sendDanmaku(now_last_query['program']['episodeTitle'])

def nextOnAir(text):
    from main import sendDanmaku
    global now_last_query
    global next_last_query
    time_now = int(time.time())
    if text.replace(' ','') == '#next':
        maxts = time_now + 3*60*60 # 3 hours from now
        timespan = '3'
    else:
        maxts = time_now + 12*60*60 # 12 hours from now
        timespan = '12'
        show_name = getShow(text.replace('#next ', ''))
        if show_name == 'ERROR':
            sendDanmaku(u'你输入的命令好像有误的喵~')
            return
    if isTBS() or timespan == '12' or next_last_query == '' or int(time.time()) > convertTime(now_last_query['endTime']):
        sendDanmaku(u'稍等一下哦，Cathy去查查放送表的喵~')
        for queryts in range(time_now, maxts, 3*60*60):
            url = "https://tvlistings.zap2it.com/api/grid"
            params = {
                'time': str(queryts),
                'device': 'X',
                'headendId': 'KY16593',
                'timespan': '3',
                'country': 'USA'
            }
            origlist = requests.get(url, params=params).json()['channels']
            list = False
            for item in origlist:
                if item['callSign'] == 'TOON' and (timespan == '12' or not isTBS(convertTime(item['events'][1]['startTime']))):
                    list = item['events']
                    for item in list:
                        if item['program']['title'] == show_name and item != list[0]:
                            sendDanmaku(u'下一次播出时间（北京时间）：')
                            time.sleep(1)
                            sendDanmaku(datetime.datetime.fromtimestamp(convertTime(item['startTime'])).strftime('%m月%d日%H:%M'))
                            if item['program']['episodeTitle'] != None:
                                time.sleep(1)
                                sendDanmaku(u'这集的标题是：')
                                time.sleep(1)
                                sendDanmaku(item['program']['episodeTitle'])
                            return
                elif timespan == '3' and item['callSign'] == 'TBS' and isTBS(convertTime(item['events'][1]['startTime'])):
                    list = item['events']
                    break
            if not list:
                sendDanmaku(u'Cathy也不知道的喵~')
                return
            if not isTBS(convertTime(list[0]['startTime'])) and queryts == time_now:
                now_last_query = list[0]
            if queryts == time_now:
                next_last_query = list[1]
    if timespan == '3':
        sendDanmaku(u'接下来播出的是：')
        time.sleep(1)
        sendDanmaku(next_last_query['program']['title'])
        if next_last_query['program']['episodeTitle'] != None:
            time.sleep(1)
            sendDanmaku(u'这集的标题是：')
            time.sleep(1)
            sendDanmaku(next_last_query['program']['episodeTitle'])
    elif timespan == '12':
        sendDanmaku(u'12小时内没有发现放送的喵~')

def newOnAir(text):
    from main import sendDanmaku
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

def isTBS(query=time.time()):
    import datetime
    return datetime.datetime.today().weekday() == 6 and int(query) > convertTime(time.strftime("%Y-%m-%dT", time.localtime()) + '01:00:00Z') and int(query) < convertTime(time.strftime("%Y-%m-%dT", time.localtime()) + '11:00:00Z')

def roomTitle(title):
    bili_cookie = OWNER_COOKIE
    url = 'https://api.live.bilibili.com/room/v1/Room/update'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Cookie': bili_cookie
    }
    data = {
        'room_id': bili_roomid,
        'title': title
    }
    response = requests.post(url, headers=headers, data=data).json()
    if response["code"] == 0:
        printlog("INFO", "Successfully changed room title to " + title)
    else:
        printlog("ERROR", "Failed to change room title to " + title)

def initStream(argv):
    printlog("INFO", "I'm going to do nothing. Write some code in plugin.py please.")