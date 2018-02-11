# -*- coding: utf-8 -*-
from generic import *
import os
import time
from lxml import etree
from datetime import datetime, timedelta
import pytz
import re

now_last_query = {'title': '', 'episodeName': '', 'airtime': 0}
next_last_query = {'title': '', 'episodeName': '', 'airtime': 0}

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
        return "Unikitty!"
    elif id == 'at':
        return "Adventure Time"
    elif id == 'ben10':
        return "Ben 10"
    elif id == 'wbb':
        return "We Bare Bears"
    elif id == 'okko':
        return "OK K.O.! Let's Be Heroes"
    elif id == 'fs':
        return "Final Space"
    else:
        return "ERROR"

def getChannel():
    status_file = open('now_channel', 'r')
    channel = status_file.readline()
    status_file.close()
    return channel.strip('\n').strip('\r')

def fixTime(_time):
    _time = time.localtime(int(_time))
    return time.strftime('%m', _time).lstrip('0') + '月' + time.strftime('%d', _time).lstrip('0') + '日' + time.strftime('%H:%M', _time).lstrip('0')

# Adapted from https://gitlab.com/ctoon/cn-schedule-fetcher
def fixShowName(show_name):
    if show_name == 'MOVIE:':
        return 'MOVIE'
    elif show_name == 'SPECIAL:':
        return 'SPECIAL'
    elif show_name == 'Amazing World of Gumball':
        return 'The Amazing World of Gumball'
    elif show_name == 'Unikitty':
        return 'Unikitty!'
    elif show_name == "OK K.O.! Let's Be Heroes!":
        return "OK K.O.! Let's Be Heroes"

    return show_name

def fixEpisodeName(episode_name):
    for title in episode_name.split('/'):
        fixed = re.sub(r'(.*?) $', 'The \\1', title)
        fixed = re.sub(r'(.*?), An$', 'An \\1', fixed)
        fixed = re.sub(r'(.*?), A$', 'A \\1', fixed)
        episode_name = episode_name.replace(title, fixed)

    return episode_name.replace('/', '; ')

def getUSEastTime(format='', yesterday=False):
    time_now = datetime.now(pytz.timezone('US/Eastern'))
    time_return = time_now
    if yesterday:
        time_return = time_now - timedelta(days=1)
    if format == '%d':
        return time_return.strftime('%d').lstrip('0')
    if format == '%m/%d/%Y':
        return time_return.strftime('%m/%d/%Y')
    return time_return

def checkSchedule(allshows, index, prev_show=''):
    global now_last_query
    global next_last_query
    date_str = allshows[index].xpath('@date')[0] + ' ' + allshows[index].xpath('@military')[0]
    show_time = pytz.timezone('US/Eastern').localize(datetime.strptime(date_str, '%m/%d/%Y %H:%M'))
    if int(time.time()) < convertTime(show_time):
        # update next_last_query
        next_last_query['title'] = fixShowName(allshows[index].xpath('@title')[0])
        next_last_query['episodeName'] = fixEpisodeName(allshows[index].xpath('@episodeName')[0])
        next_last_query['airtime'] = convertTime(show_time)
        # update now_last_query
        if prev_show != '':
            show = prev_show
        else:
            show = allshows[index-1]
        date_str = show.xpath('@date')[0] + ' ' + show.xpath('@military')[0]
        show_time = pytz.timezone('US/Eastern').localize(datetime.strptime(date_str, '%m/%d/%Y %H:%M'))
        now_last_query['title'] = fixShowName(show.xpath('@title')[0])
        now_last_query['episodeName'] = fixEpisodeName(show.xpath('@episodeName')[0])
        now_last_query['airtime'] = convertTime(show_time)
        return True

def getSchedule(channel='undefined', showName='undefined'): # if showName is defined then we need to query 12 hours
    from main import sendDanmaku
    sendDanmaku(u'稍等一下哦，Cathy去查查放送表的喵~')
    if channel == 'cn' or channel == 'as' or getChannel() == 'cn' or getChannel() == 'as' or getChannel() == 'offair':
        url = 'https://www.adultswim.com/adultswimdynsched/xmlServices/' + getUSEastTime('%d') + '.EST.xml'
        allshows = etree.XML(requests.get(url).content)
        cn_start = False
        for index, show in enumerate(allshows):
            if show.xpath('@blockName')[0] == 'AdultSwim':
                continue # skip all [as] entries
            if not cn_start: # parse yesterday's [adult swim] schedule, from 0:00
                cn_start = True
                url = 'https://www.adultswim.com/adultswimdynsched/asXml/' + getUSEastTime('%d', True) + '.EST.xml'
                allshows_aswim = etree.XML(requests.get(url).content).xpath('//allshows/show[@date="' + getUSEastTime('%m/%d/%Y') + '"]')
                for index_aswim, show_aswim in enumerate(allshows_aswim):
                    if show_aswim == allshows_aswim[-1]: # last [as] entry? save it
                        prev_show = show_aswim
                    if checkSchedule(allshows_aswim, index_aswim) and showName == 'undefined':
                        return True
                # parse the first entry of CN schedule
                checkflag = checkSchedule(allshows, index, prev_show)
                if checkflag and showName == 'undefined':
                    return True
            # parse the rest of CN schedule
            checkflag = checkSchedule(allshows, index)
            if checkflag and showName == 'undefined':
                return True
            if show == allshows[-1]: # parse today's [adult swim] schedule
                url = 'https://www.adultswim.com/adultswimdynsched/asXml/' + getUSEastTime('%d') + '.EST.xml'
                allshows_aswim = etree.XML(requests.get(url).content).xpath('//allshows/show[@date="' + getUSEastTime('%m/%d/%Y') + '"]')
                for index_aswim, show_aswim in enumerate(allshows_aswim):
                    if checkSchedule(allshows_aswim, index_aswim) and showName == 'undefined':
                        return True
        return False # not found

def nowOnAir():
    from main import sendDanmaku
    if getChannel() == 'offair':
        sendDanmaku(u'因为版权原因，现在什么都不会播的喵~')
        return
    global now_last_query
    global next_last_query
    if now_last_query['title'] == '' or int(time.time()) > next_last_query['airtime']:
        if not getSchedule():
            sendDanmaku(u'Cathy也不知道的喵~')
            return
    sendDanmaku(u'正在播出的是：')
    time.sleep(1)
    sendDanmaku(now_last_query['title'])
    if now_last_query['episodeName'] != None:
        time.sleep(1)
        sendDanmaku(u'这集的标题是：')
        time.sleep(1)
        sendDanmaku(now_last_query['episodeName'])

def nextOnAir(text):
    from main import sendDanmaku
    global now_last_query
    global next_last_query
    if text.replace(' ','') == '#next': # literally what's coming up next
        if next_last_query['title'] == '' or int(time.time()) > next_last_query['airtime']:
            if not getSchedule():
                sendDanmaku(u'Cathy也不知道的喵~')
                return
        if isTBS(next_last_query['airtime']):
            sendDanmaku(u'因为版权原因，短时间内什么都不会播的喵~')
            return
        sendDanmaku(u'接下来播出的是：')
        time.sleep(1)
        sendDanmaku(next_last_query['title'])
        if next_last_query['episodeName'] != None:
            time.sleep(1)
            sendDanmaku(u'这集的标题是：')
            time.sleep(1)
            sendDanmaku(next_last_query['episodeName'])
    else:
        show_name = getShow(text.replace('#next ', ''))
        if show_name == 'ERROR':
            sendDanmaku(u'你输入的命令好像有误的喵~')
            return
        sendDanmaku(u'呜喵，这个功能被暂时禁用了> <')
        #getSchedule(showName=show_name)

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
        if item[8] == "Cartoon Network" or item[8] == "Adult Swim" or item[8] == "TBS" or item[8] == "TNT":
            if text.replace(' ','') != '#new' and fixShowName(item[9]) == show_name:
                sendDanmaku(u'下一次首播时间（北京时间）：')
                time.sleep(1)
                sendDanmaku(fixTime(item[0]))
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
                sendDanmaku(fixTime(item[0]))
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

def isTBS(query='undefined'):
    if query == 'undefined':
        query = time.time()
    return datetime.today().weekday() == 6 and int(query) > convertTime(datetime.now().replace(hour=9,minute=0,second=0,microsecond=0)) and int(query) < convertTime(datetime.now().replace(hour=19,minute=0,second=0,microsecond=0))

def roomTitle(title):
    bili_cookie = OWNER_COOKIE
    url = 'https://api.live.bilibili.com/room/v1/Room/update'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Cookie': bili_cookie,
        'User-Agent': ''
    }
    data = {
        'room_id': bili_roomid,
        'title': title,
    }
    response = requests.post(url, headers=headers, data=data).json()
    if response["code"] == 0:
        printlog("INFO", "Successfully changed room title to " + title)
    else:
        printlog("ERROR", "Failed to change room title to " + title)

def initStream(argv):
    printlog("INFO", "I'm going to do nothing. Write some code in plugin.py please.")