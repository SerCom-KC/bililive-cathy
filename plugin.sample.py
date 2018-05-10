# -*- coding: utf-8 -*-
from generic import *
import os
import time
from lxml import etree
from datetime import datetime, timedelta
import pytz
import re

def commandParse(source, text, time):
    from main import sendReply
    if (source["from"] == "bili-danmaku" or source["from"] == "bili-msg") and str(source["uid"]) == getConfig('host', 'uid'):
        if text == '#status':
            sendReply(source, [u'Cathy在的喵~'])
    if text == '#now':
        nowOnAir(source)
        #sendReply(source, [u'呜，Cathy的时间表被KC没收了~'])
    elif text.find('#new') == 0:
        #newOnAir(source, text)
        sendReply(source, [u'这个功能被禁用了，非常抱歉呜喵QAQ'])
    elif text.find('#next') == 0:
        nextOnAir(source, text)
        #sendReply(source, [u'呜，Cathy的时间表被KC没收了~'])
    elif text.find(u'字幕') != -1:
        sendReply(source, [u'需要英文字幕的话请前往备用直播间哦~'])
    else:
        return False
    return True

def getShow(id):
    id = id.lower()
    if id == 'tawog' or id == "376453":
        return "The Amazing World of Gumball"
    elif id == 'cl' or id == "403152":
        return "Clarence"
    elif id == 'ttg' or id == "393474":
        return "Teen Titans Go!"
    elif id == 'tt' or id == "326561":
        return "Teen Titans"
    elif id == 'uni' or id == "442472":
        return "Unikitty!"
    elif id == 'at' or id == "368594":
        return "Adventure Time"
    elif id == 'ben10' or id == "438472":
        return "Ben 10"
    elif id == 'wbb' or id == "419032":
        return "We Bare Bears"
    elif id == 'okko' or id == "440832":
        return "OK K.O.! Let's Be Heroes"
    elif id == 'fs' or id == "444812":
        return "Final Space"
    elif id == 'aao' or id == "444772":
        return "Apple & Onion"
    elif id == 'su' or id == '399692':
        return "Steven Universe"
    else:
        return "ERROR"

def getShowID(id):
    id = id.lower()
    if id == 'tawog':
        return "376453"
    elif id == 'cl':
        return "403152"
    elif id == 'ttg':
        return "393474"
    elif id == 'tt':
        return "326561"
    elif id == 'uni':
        return "442472"
    elif id == 'at':
        return "368594"
    elif id == 'ben10':
        return "438472"
    elif id == 'wbb':
        return "419032"
    elif id == 'okko':
        return "440832"
    elif id == 'fs':
        return "444812"
    elif id == 'aao':
        return "444772"
    elif id == 'su':
        return "399692"
    elif id.isdigit():
        return id
    else:
        return "ERROR"

def getChannel():
    return getConfig('extras', 'now_channel')

def fixTime(_time):
    cst_offset = int(pytz.timezone('Asia/Shanghai').utcoffset(datetime.now()).total_seconds())
    _time = time.gmtime(int(_time)+cst_offset)
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

def getUSEastTime(format='', yesterday=False, tomorrow=False):
    time_now = datetime.now(pytz.timezone('US/Eastern'))
    time_return = time_now
    if yesterday:
        time_return = time_now - timedelta(days=1)
    elif tomorrow:
        time_return = time_now + timedelta(days=1)
    if format == '%d' or format == '%m':
        return time_return.strftime(format).lstrip('0')
    if format == '%Y' or format == '%m/%d/%Y':
        return time_return.strftime(format)
    return time_return

def getNextShowing(showId):
    url = 'https://www.adultswim.com/adultswimdynsched/xmlServices/ScheduleServices'
    params = {
        'methodName': 'getAllShowingsByID',
        'showId': showId,
        'timezone': 'EST'
    }
    allShowings = etree.XML(requests.get(url, params=params, timeout=3).content)
    try:
        errtmp = allShowings[0]
    except IndexError:
        return False # no showings, or invalid showId
    for show in allShowings:
        # We need to manually add the year part here.
        # Since this API usually returns data up to two weeks, we can use this trick:
        # If it's December, and there's a showing on January, that must be next year's stuff;
        # Otherwise, this showing should be this year.
        if getUSEastTime('%m') == '12' and show.xpath('@date')[0].find('January'):
            year = str(int(getUSEastTime('%Y')) + 1)
        else:
            year = getUSEastTime('%Y')
        date_str = show.xpath('@time')[0] + ' ' + show.xpath('@date')[0] + ' ' + year
        show_time = pytz.timezone('US/Eastern').localize(datetime.strptime(date_str, '%I:%M %p %B %d %Y'))
        if int(time.time()) < convertTime(show_time):
            return {'episodeName': fixEpisodeName(show.xpath('@episode')[0]), 'airtime': convertTime(show_time)}
            break
    printlog('ERROR', 'An unexpected error occurred when looking up next showing for showId ' + showId + '.')
    return False #errors

def checkSchedule(allshows, index, prev_show=''):
    date_str = allshows[index].xpath('@date')[0] + ' ' + allshows[index].xpath('@military')[0]
    show_time = pytz.timezone('US/Eastern').localize(datetime.strptime(date_str, '%m/%d/%Y %H:%M'))
    if int(time.time()) < convertTime(show_time):
        # update next_last_query
        if allshows[index].xpath('@title')[0] == "Cartoon Network": # fetch episodeName manually
            setConfig('extras', 'next_title', getShow(allshows[index].xpath('@showId')[0]))
            url = 'https://www.adultswim.com/adultswimdynsched/xmlServices/ScheduleServices'
            params = {
                'methodName': 'getEpisodeDesc',
                'showId': allshows[index].xpath('@showId')[0],
                'episodeId': allshows[index].xpath('@episodeId')[0],
                'isFeatured': allshows[index].xpath('@isFeatured')[0]
            }
            setConfig('extras', 'next_episodeName', fixEpisodeName(etree.XML(requests.get(url, params=params, timeout=3).content).xpath("//Desc/episodeDesc/text()")[0]))
        else:
            setConfig('extras', 'next_title', fixShowName(allshows[index].xpath('@title')[0]))
            setConfig('extras', 'next_episodeName', fixEpisodeName(allshows[index].xpath('@episodeName')[0]))
        setConfig('extras', 'next_airtime', convertTime(show_time))
        # update now_last_query
        if prev_show != '':
            show = prev_show
        else:
            show = allshows[index-1]
        date_str = show.xpath('@date')[0] + ' ' + show.xpath('@military')[0]
        show_time = pytz.timezone('US/Eastern').localize(datetime.strptime(date_str, '%m/%d/%Y %H:%M'))
        if show.xpath('@title')[0] == "Cartoon Network": # fetch episodeName manually
            setConfig('extras', 'now_title', getShow(show.xpath('@showId')[0]))
            url = 'https://www.adultswim.com/adultswimdynsched/xmlServices/ScheduleServices'
            params = {
                'methodName': 'getEpisodeDesc',
                'showId': show.xpath('@showId')[0],
                'episodeId': show.xpath('@episodeId')[0],
                'isFeatured': show.xpath('@isFeatured')[0]
            }
            setConfig('extras', 'now_episodeName', fixEpisodeName(etree.XML(requests.get(url, params=params, timeout=3).content).xpath("//Desc/episodeDesc/text()")[0]))
        else:
            setConfig('extras', 'now_title', fixShowName(show.xpath('@title')[0]))
            setConfig('extras', 'now_episodeName', fixEpisodeName(show.xpath('@episodeName')[0]))
        setConfig('extras', 'now_airtime', convertTime(show_time))
        printlog("INFO", "Now on air: " + getConfig('extras', 'now_title') + ' - ' + getConfig('extras', 'now_episodeName'))
        return True
    return False

def getSchedule(source=None, channel='undefined'):
    from main import sendReply
    now_last_query = {'title': getConfig('extras', 'now_title'), 'episodeName': getConfig('extras', 'now_episodeName'), 'airtime': int(getConfig('extras', 'now_airtime'))}
    next_last_query = {'title': getConfig('extras', 'next_title'), 'episodeName': getConfig('extras', 'next_episodeName'), 'airtime': int(getConfig('extras', 'next_airtime'))}
    if now_last_query['title'] != '' and next_last_query['title'] != '' and int(time.time()) < next_last_query['airtime']: # needs update
        return True
    if source:
        sendReply(source, [u'稍等一下哦，Cathy去查查放送表的喵~'])
    if channel == 'cn' or channel == 'as' or getChannel() == 'cn' or getChannel() == 'as' or getChannel() == 'offair':
        url = 'https://www.adultswim.com/adultswimdynsched/xmlServices/' + getUSEastTime('%d') + '.EST.xml'
        allshows = etree.XML(requests.get(url, timeout=3).content)
        cn_start = False
        for index, show in enumerate(allshows):
            if show.xpath('@blockName')[0] == 'AdultSwim':
                if not cn_start:
                    continue # skip all [as] entries
                else:
                    prev_show = allshows[index-1] # save the last CN entry of today
                    break
            if not cn_start: # parse yesterday's [adult swim] schedule, from 0:00
                cn_start = True
                url = 'https://www.adultswim.com/adultswimdynsched/asXml/' + getUSEastTime('%d', yesterday=True) + '.EST.xml'
                allshows_aswim = etree.XML(requests.get(url, timeout=3).content).xpath('//allshows/show[@date="' + getUSEastTime('%m/%d/%Y') + '"]')
                for index_aswim, show_aswim in enumerate(allshows_aswim):
                    if checkSchedule(allshows_aswim, index_aswim):
                        return True
                prev_show = show_aswim
                # parse the first entry of CN schedule
                checkflag = checkSchedule(allshows, index, prev_show)
                if checkflag:
                    return True
            # parse the rest of CN schedule
            checkflag = checkSchedule(allshows, index)
            if checkflag:
                return True
        # parse today's [adult swim] schedule
        url = 'https://www.adultswim.com/adultswimdynsched/asXml/' + getUSEastTime('%d') + '.EST.xml'
        allshows_aswim = etree.XML(requests.get(url, timeout=3).content).xpath('//allshows/show[@date="' + getUSEastTime('%m/%d/%Y') + '"]')
        for index_aswim, show_aswim in enumerate(allshows_aswim):
            if index_aswim == 0:
                checkflag = checkSchedule(allshows_aswim, index_aswim, prev_show)
            else:
                checkflag = checkSchedule(allshows_aswim, index_aswim)
            if checkflag:
                return True
        prev_show = show_aswim
        # parse the first [as] entry of next day in today's schedule
        allshows_aswim = etree.XML(requests.get(url, timeout=3).content).xpath('//allshows/show[@date="' + getUSEastTime('%m/%d/%Y', tomorrow=True) + '"]')
        checkflag = checkSchedule(allshows_aswim, 0, prev_show)
        if checkflag:
            return True
        printlog('ERROR', 'An error occurred when parsing the schedule. The time now is ' + time.ctime())
        return False # not found

def nowOnAir(source):
    from main import sendReply
    if getChannel() == 'offair':
        sendReply(source, [u'现在什么都不会播的喵~'])
        return
    now_last_query = {'title': getConfig('extras', 'now_title'), 'episodeName': getConfig('extras', 'now_episodeName'), 'airtime': int(getConfig('extras', 'now_airtime'))}
    next_last_query = {'title': getConfig('extras', 'next_title'), 'episodeName': getConfig('extras', 'next_episodeName'), 'airtime': int(getConfig('extras', 'next_airtime'))}
    if not getSchedule(source):
        sendReply(source, [u'Cathy也不知道的喵~'])
        return
    if now_last_query['title'] == "[AdultSwim]" or now_last_query['title'] == "Cartoon Network": # parse failed
        sendReply(source, [u'Cathy也不知道的喵~'])
        return
    result = [u'正在播出的是：']
    if now_last_query['title'] == "MOVIE" or now_last_query['title'] == "SPECIAL":
        result.append(now_last_query['episodeName'])
    else:
        result.append(now_last_query['title'])
        if now_last_query['episodeName'] != None and now_last_query['episodeName'] != '':
            result.append(u'这集的标题是：')
            result.append(now_last_query['episodeName'])
    sendReply(source, result)

def nextOnAir(source, text):
    from main import sendReply
    if getChannel() == 'offair':
        sendReply(source, [u'晚点再来喵~'])
        return
    next_last_query = {'title': getConfig('extras', 'next_title'), 'episodeName': getConfig('extras', 'next_episodeName'), 'airtime': int(getConfig('extras', 'next_airtime'))}
    if text.replace(' ','') == '#next': # literally what's coming up next
        if not getSchedule(source):
            sendReply(source, [u'Cathy也不知道的喵~'])
            return
        if next_last_query['title'] == "[AdultSwim]" or next_last_query['title'] == "Cartoon Network":
            sendReply(source, [u'Cathy也不知道的喵~'])
            return
        result = [u'接下来播出的是：']
        if next_last_query['title'] == "MOVIE" or next_last_query['title'] == "SPECIAL":
            result.append(next_last_query['episodeName'])
            return
        else:
            result.append(next_last_query['title'])
            if next_last_query['episodeName'] != None and next_last_query['episodeName'] != '':
                result.append(u'这集的标题是：')
                result.append(next_last_query['episodeName'])
        sendReply(source, result)
    else:
        show_id = getShowID(text.replace('#next ', ''))
        if show_id == 'ERROR':
            sendReply(source, [u'你输入的命令好像有误的喵~'])
            return
        next_showing = getNextShowing(show_id)
        if next_showing:
            sendReply(source, [u'下一次播出时间（北京时间）：', fixTime(next_showing['airtime']), u'这集的标题是：', next_showing['episodeName']])
        else:
            result = [u'在可预见的未来没有发现放送的喵~']
            if getShow(text.replace('#next ', '')) == 'ERROR':
                result.append(u'也许是你输错了数字ID喵？')
            sendReply(source, result)

def newOnAir(source, text):
    from main import sendReply
    if text.replace(' ','') != '#new':
        show_name = getShow(text.replace('#new ', ''))
        if show_name == 'ERROR':
            sendReply(source, [u'你输入的命令好像有误的喵~'])
            return
    url = "https://catting.net/nep.json"
    list = requests.get(url, timeout=3).json()
    for item in list:
        if item[8] == "Cartoon Network" or item[8] == "Adult Swim" or item[8] == "TBS" or item[8] == "TNT":
            if text.replace(' ','') != '#new' and fixShowName(item[9]) == show_name:
                sendReply(source, [u'下一次首播时间（北京时间）：', fixTime(item[0]), u'这集的标题是：', item[10]])
                return
            elif text.replace(' ','') == '#new':
                sendReply(source, [u'即将在' + item[8] + u'首播', item[9], u'播出时间（北京时间）：', fixTime(item[0]), u'这集的标题是：', item[10]])
                return
    if show_name:
        sendReply(source, [u'两周内没有发现首播的喵~'])
    else:
        sendReply(source, [u'Cathy也不知道的喵~'])

def roomTitle(title):
    url = 'https://api.live.bilibili.com/mhand/Assistant/updateRoomInfo'
    params = {
        'access_key': getConfig('host', 'accesskey')
    }
    data = {
        'roomId': bili_roomid,
        'title': title
    }
    response = bilireq(url, params=params, data=data).json()
    if response["code"] == 0:
        printlog("INFO", "Successfully changed room title to " + title)
    else:
        printlog("ERROR", "Failed to change room title to " + title + ". API says " + response["message"])

def initStream(argv):
    printlog("INFO", "I'm going to do nothing. Write some code in plugin.py please.")
