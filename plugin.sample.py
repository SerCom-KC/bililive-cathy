# -*- coding: utf-8 -*-
from generic import *
import os
import time
from lxml import etree
from datetime import datetime, timedelta
import pytz
import re

def commandParse(source, text):
    from main import sendReply
    if text == '#status':
        if (source["from"] == "bili-danmaku" or source["from"] == "bili-msg") and str(source["uid"]) == getConfig('host', 'uid'):
            sendReply(source, ['Cathy在的喵~'])
        else:
            return False
    elif text == '#now':
        nowOnAir(source)
        #sendReply(source, ['呜，Cathy的时间表被KC没收了~'])
    elif text.find('#new') == 0:
        newOnAir(source, text)
        #sendReply(source, ['这个功能被禁用了，非常抱歉呜喵QAQ'])
    elif text.find('#next') == 0:
        nextOnAir(source, text)
        #sendReply(source, ['呜，Cathy的时间表被KC没收了~'])
    elif text.find('字幕') != -1:
        sendReply(source, ['需要英文字幕的话请前往备用直播间喵~'])
    elif text == '#help':
        if source["from"] == "bili-danmaku":
            sendReply(source, ['呜喵~太多了不能在弹幕里发的喵！', '请在私信里发送这个命令的喵！'])
        else:
            responses = [
                '当前支持的命令有以下这些的喵~',
                '',
                '#now',
                '如果你想知道B站直播间正在放的是什么剧的话，请发送这个命令喵~',
                '不过要注意的是，如果当前播出的剧是11分钟一集的话，有可能会显示两集的标题（也就是当前的半小时档），而且跟实际放送顺序不一定相同的喵~',
                '',
                '#next',
                '如果你想知道B站直播间接下来会放什么剧的话，请发送这个命令喵~',
                '跟#now一样有可能会显示两集的标题（也就是接下来的半小时档），所以请一定按实际情况为准的喵~',
                '想知道自己想看的剧什么时候放的话，请在后面加上这个剧的缩写或者数字ID（特纳API中使用的ID，不知道的话不要乱试喵）',
                '比如 #next su 这样的喵~',
                '但是请注意多数情况下是重播而不是更新的喵~',
                '支持的缩写列表请发送 #help list 查看的喵~',
                '',
                '#new',
                '如果你想知道自己想看的剧什么时候更新的话，请使用这个命令喵~',
                '同样也需要在后面加上这个剧的缩写，比如 #new su 这样的喵~',
                '请注意这个命令查到的都是TV首播，也就是说如果有网络首播的话这个命令是查不到的喵~',
                '如果不指定是哪个剧的话，将会返回CARTOON NETWORK/[adult swim]接下来要TV首播的内容喵~',
                '并且这个命令的数据源是第三方（TV Guide）而不是官方，所以请一定要以实际情况为准的喵~',
                '支持的缩写列表请发送 #help list 查看的喵~'
            ]
            if source["from"] == "telegram-inlinequery" or source["from"] == "telegram-private":
                responses.extend((
                    '',
                    '使用Telegram的小伙伴还可以在与我的私聊中使用 / 作为命令开头的喵~',
                    '同时也可以在任意对话中使用inline模式唤起我的喵~不过这种情况还是只能用 # 作为命令开头的喵~',
                    '此外目前在inline模式中使用#new命令的话，我可以一次性返回最多5个结果的喵~',
                    '点击结果还可以显示更多信息的喵~来试试吧喵~'
                ))
            sendReply(source, responses)
    elif text == '#help list':
        if source["from"] == "bili-danmaku":
            sendReply(source, ['呜喵~太多了不能在弹幕里发的喵！', '请在私信里发送这个命令的喵！'])
        else:
            sendReply(source, ['当前支持的缩写列表：',
                               'tawog - The Amazing World of Gumball',
                               'cl - Clarence',
                               'ttg - Teen Titans Go!',
                               'tt - Teen Titans',
                               'uni - Unikitty!',
                               'at - Adventure Time',
                               'ben10 - Ben 10',
                               'wbb - We Bare Bears',
                               'okko - OK K.O.! Let\'s Be Heroes',
                               'fs - Final Space',
                               'aao - Apple & Onion',
                               'su - Steven Universe',
                               'ppg2016 - The Powerpuff Girls (2016)',
                               'flcl - FLCL',
                               'ram - Rick and Morty',
                               'mp - Mr. Pickles',
                               'mm - Mighty Magiswords',
                               '如果你想看的特纳剧不在这个列表里的话，请联系 @SerCom_KC 追加的喵~'])
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
    elif id == 'su' or id == "399692":
        return "Steven Universe"
    elif id == 'ppg2016' or id == "425772":
        return "The Powerpuff Girls"
    elif id == 'flcl' or id == "447432":
        return "FLCL"
    elif id == 'ram' or id == "401312":
        return "Rick and Morty"
    elif id == 'mp' or id == "398292":
        return "Mr. Pickles"
    elif id == 'mm' or id == "423572":
        return "Mighty Magiswords"
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
    elif id == 'ppg2016':
        return "425772"
    elif id == 'flcl':
        return "447432"
    elif id == 'ram':
        return "401312"
    elif id == 'mp':
        return "398292"
    elif id == 'mm':
        return "423572"
    elif id.isdigit():
        return id
    else:
        return "ERROR"

def getThumbnailByShow(show_name):
    if show_name == "The Amazing World of Gumball":
        return "https://i.cdn.turner.com/v5cache/CARTOON/site/Images/i69/Gumball_150x150.jpg"
    elif show_name == "Clarence":
        return "https://i.cdn.turner.com/v5cache/CARTOON/site/Images/i78/clarence_150x150.jpg"
    elif show_name == "Teen Titans Go!":
        return "https://i.cdn.turner.com/v5cache/CARTOON/site/Images/i74/ttg_150x150.jpg"
    elif show_name == "Teen Titans":
        return "https://i.cdn.turner.com/v5cache/CARTOON/site/Images/i69/TeenTitans_150x150.jpg"
    elif show_name == "Unikitty!":
        return "https://i.cdn.turner.com/v5cache/CARTOON/site/Images/i221/unikitty_showpickericon_150x150.png"
    elif show_name == "Adventure Time":
        return "https://i.cdn.turner.com/v5cache/CARTOON/site/Images/i69/AT_150x150.jpg"
    elif show_name == "Ben 10":
        return "https://i.cdn.turner.com/v5cache/CARTOON/site/Images/i182/ben17_150x150.jpg"
    elif show_name == "We Bare Bears":
        return "https://i.cdn.turner.com/v5cache/CARTOON/site/Images/i101/wbb_150x150.jpg"
    elif show_name == "OK K.O.! Let's Be Heroes":
        return "https://i.cdn.turner.com/v5cache/CARTOON/site/Images/i195/okko_showpicker_150x150.png"
    elif show_name == "Final Space":
        return ""
    elif show_name == "Apple & Onion":
        return "https://i.cdn.turner.com/v5cache/CARTOON/site/Images/i248/ao_showpicker_150x150.jpg"
    elif show_name == "Steven Universe":
        return "https://i.cdn.turner.com/v5cache/CARTOON/site/Images/i81/su_showpicker_150x150_v6.jpg"
    elif show_name == "The Powerpuff Girls":
        return "https://i.cdn.turner.com/v5cache/CARTOON/site/Images/i125/ppg_showpicker_bubbles_150x150.png"
    elif show_name == "FLCL":
        return ""
    elif show_name == "Rick and Morty":
        return ""
    elif show_name == "Mr. Pickles":
        return ""
    elif show_name == "Mighty Magiswords":
        return "https://i.cdn.turner.com/v5cache/CARTOON/site/Images/i97/magiswords_showpicker_150x150.jpg"
    else:
        return ""

def getChannel():
    return getConfig('extras', 'now_channel')

def fixTime(_time):
    cst_offset = int(pytz.timezone('Asia/Shanghai').utcoffset(datetime.now()).total_seconds())
    _time = time.gmtime(int(_time)+cst_offset)
    hm = time.strftime('%H:%M', _time)
    hm = hm.replace('0', '', 1) if hm[0] == '0' else hm
    return time.strftime('%m', _time).lstrip('0') + '月' + time.strftime('%d', _time).lstrip('0') + '日' + hm

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
        fixed = re.sub(r'(.*?), The$', 'The \\1', fixed)
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
        if allshows[index].xpath('@title')[0] == "Cartoon Network":
            title_fixed = getShow(allshows[index].xpath('@showId')[0])
            if title_fixed == 'ERROR': # ID not in our database yet
                title_fixed = "（欸，是叫什么来着喵？）"
            setConfig('extras', 'next_title', title_fixed)
        else:
            setConfig('extras', 'next_title', fixShowName(allshows[index].xpath('@title')[0]))
        # fetch episodeName manually to avoid "The" problem in https://gitlab.com/ctoon/cn-schedule-fetcher/issues/1 since getEpisodeDesc returns standard ", The"
        url = 'https://www.adultswim.com/adultswimdynsched/xmlServices/ScheduleServices'
        params = {
            'methodName': 'getEpisodeDesc',
            'showId': allshows[index].xpath('@showId')[0],
            'episodeId': allshows[index].xpath('@episodeId')[0],
            'isFeatured': 'N' #allshows[index].xpath('@isFeatured')[0]
        }
        setConfig('extras', 'next_episodeName', fixEpisodeName(etree.XML(requests.get(url, params=params, timeout=3).content).xpath("//Desc/episodeDesc/text()")[0]))
        setConfig('extras', 'next_airtime', convertTime(show_time))
        # update now_last_query
        if prev_show != '':
            show = prev_show
        else:
            show = allshows[index-1]
        date_str = show.xpath('@date')[0] + ' ' + show.xpath('@military')[0]
        show_time = pytz.timezone('US/Eastern').localize(datetime.strptime(date_str, '%m/%d/%Y %H:%M'))
        if show.xpath('@title')[0] == "Cartoon Network":
            title_fixed = getShow(show.xpath('@showId')[0])
            if title_fixed == 'ERROR': # ID not in our database yet
                title_fixed = "（欸，是叫什么来着喵？）"
            setConfig('extras', 'now_title', title_fixed)
        else:
            setConfig('extras', 'now_title', fixShowName(show.xpath('@title')[0]))
        # fetch episodeName manually to avoid "The" problem in https://gitlab.com/ctoon/cn-schedule-fetcher/issues/1 since getEpisodeDesc returns standard ", The"
        url = 'https://www.adultswim.com/adultswimdynsched/xmlServices/ScheduleServices'
        params = {
            'methodName': 'getEpisodeDesc',
            'showId': show.xpath('@showId')[0],
            'episodeId': show.xpath('@episodeId')[0],
            'isFeatured': 'N' #show.xpath('@isFeatured')[0]
        }
        setConfig('extras', 'now_episodeName', fixEpisodeName(etree.XML(requests.get(url, params=params, timeout=3).content).xpath("//Desc/episodeDesc/text()")[0]))
        setConfig('extras', 'now_airtime', convertTime(show_time))
        printlog("INFO", "Now on air: " + getConfig('extras', 'now_title') + ' - ' + getConfig('extras', 'now_episodeName'))
        return True
    return False

def getSchedule(source=None, channel='undefined'):
    from main import sendReply, sendBusy
    now_last_query = {'title': getConfig('extras', 'now_title'), 'episodeName': getConfig('extras', 'now_episodeName'), 'airtime': int(getConfig('extras', 'now_airtime'))}
    next_last_query = {'title': getConfig('extras', 'next_title'), 'episodeName': getConfig('extras', 'next_episodeName'), 'airtime': int(getConfig('extras', 'next_airtime'))}
    if now_last_query['title'] != '' and next_last_query['title'] != '' and int(time.time()) < next_last_query['airtime']: # needs update
        return True
    if source:
        sendBusy(source, '稍等一下哦，Cathy去查查放送表的喵~')
    if channel == 'cn' or channel == 'as' or getChannel() == 'cn' or getChannel() == 'as' or getChannel() == 'restrict':
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
    #if getChannel() == 'restrict':
    #    sendReply(source, ['现在什么都不会播的喵~'])
    #    return
    if source["from"] != "telegram-inlinequery":
        now_last_query = {'title': getConfig('extras', 'now_title'), 'episodeName': getConfig('extras', 'now_episodeName'), 'airtime': int(getConfig('extras', 'now_airtime'))}
        if not getSchedule(source):
            sendReply(source, ['Cathy也不知道的喵~'])
            return
        if now_last_query['title'] == "[AdultSwim]" or now_last_query['title'] == "Cartoon Network": # parse failed
            sendReply(source, ['Cathy也不知道的喵~'])
            return
        result = ['正在播出的是：']
        if now_last_query['title'] == "MOVIE" or now_last_query['title'] == "SPECIAL":
            result.append(now_last_query['episodeName'])
        else:
            result.append(now_last_query['title'])
            if now_last_query['episodeName'] != None and now_last_query['episodeName'] != '':
                result.append('这集的标题是：')
                result.append(now_last_query['episodeName'])
    else:
        try:
            url = "https://mobilelistings.tvguide.com/Listingsweb/ws/rest/schedules/80001/start/" + str(int(time.time())) + "/duration/1"
            list = requests.get(url, params = {"channelsourceids": "3460|*,410|*,427|*", "formattype": "json"}, timeout=3).json()
            for channel in list:
                if channel["Channel"]["Name"] == "TOON":
                    program = channel["ProgramSchedules"][0]
                    if program["TVObject"] and int(program["TVObject"]["SeasonNumber"]) != 0 and int(program["TVObject"]["EpisodeNumber"]) != 0:
                        SeasonNumber = '0' + str(program["TVObject"]["SeasonNumber"]) if int(program["TVObject"]["SeasonNumber"]) < 10 else str(program["TVObject"]["SeasonNumber"])
                        EpisodeNumber = '0' + str(program["TVObject"]["EpisodeNumber"]) if int(program["TVObject"]["EpisodeNumber"]) < 10 else str(program["TVObject"]["EpisodeNumber"])
                        EpisodeNo = 'S' + SeasonNumber + 'E' + EpisodeNumber + ' '
                    else:
                        EpisodeNo = '未知集数 '
                    message_text = '<b>' + program["Title"] + ' '
                    message_text += EpisodeNo if EpisodeNo != '未知集数 ' else ''
                    message_text += '- ' + program["EpisodeTitle"] + '</b>\n<i>当前正在' + channel["Channel"]["Name"] + '放送中，' + fixTime(program["StartTime"]) + '-' + fixTime(program["EndTime"]) + '，' + program["Rating"].replace('@', '-') + '</i>\n'
                    message_text += program["CopyText"] if program["CopyText"] else '暂无简介'
                    result = [{
                        "type": "article",
                        "id": str(int(source["id"]) + int(time.time())),
                        "title": program["EpisodeTitle"],
                        "input_message_content": {
                            "message_text": message_text,
                            "parse_mode": 'HTML'
                        },
                        "description": program["Title"] + ' - ' + fixTime(program["StartTime"]),
                        "thumb_url": getThumbnailByShow(fixShowName(program["Title"]))
                    }]
                    break
        except Exception:
            sendReply(source, ['Cathy也不知道的喵~'])
            return
    sendReply(source, result, "telegram-inlinequeryresult" if source["from"] == "telegram-inlinequery" else "text")

def nextOnAir(source, text):
    from main import sendReply
    #if getChannel() == 'restrict' and source["from"] != "telegram-inlinequery":
    #    sendReply(source, ['晚点再来喵~'])
    #    return
    if source["from"] != "telegram-inlinequery":
        next_last_query = {'title': getConfig('extras', 'next_title'), 'episodeName': getConfig('extras', 'next_episodeName'), 'airtime': int(getConfig('extras', 'next_airtime'))}
        if text.replace(' ','') == '#next': # literally what's coming up next
            if not getSchedule(source):
                sendReply(source, ['Cathy也不知道的喵~'])
                return
            if next_last_query['title'] == "[AdultSwim]" or next_last_query['title'] == "Cartoon Network":
                sendReply(source, ['Cathy也不知道的喵~'])
                return
            result = ['接下来播出的是：']
            if next_last_query['title'] == "MOVIE" or next_last_query['title'] == "SPECIAL":
                result.append(next_last_query['episodeName'])
            else:
                result.append(next_last_query['title'])
                if next_last_query['episodeName'] != None and next_last_query['episodeName'] != '':
                    result.append('这集的标题是：')
                    result.append(next_last_query['episodeName'])
            sendReply(source, result)
            return
        else:
            show_id = getShowID(text.replace('#next ', ''))
            if show_id == 'ERROR':
                sendReply(source, ['你输入的命令好像有误的喵~'])
                return
            next_showing = getNextShowing(show_id)
            if next_showing:
                sendReply(source, ['下一次播出时间（北京时间）：', fixTime(next_showing['airtime']), '这集的标题是：', next_showing['episodeName']])
            else:
                result = ['在可预见的未来没有发现放送的喵~']
                if getShow(text.replace('#next ', '')) == 'ERROR':
                    result.append('也许是你输错了数字ID喵？')
                sendReply(source, result)
            return
    else:
        if text.replace('#next ', '').isdigit():
            sendReply(source, ['呜喵~inline模式不支持数字ID的喵~', '请使用缩写的喵~'])
            return
        result = []
        skip_first = True
        try:
            if text.replace(' ','') == '#next':
                url = "https://mobilelistings.tvguide.com/Listingsweb/ws/rest/schedules/80001/start/" + str(int(time.time())) + "/duration/600"
            else:
                if getShow(text.replace('#next ', '')) == 'ERROR':
                    sendReply(source, ['你输入的命令好像有误的喵~'])
                    return
                url = "https://mobilelistings.tvguide.com/Listingsweb/ws/rest/schedules/80001/start/" + str(int(time.time())) + "/duration/20160"
            list = requests.get(url, params = {"channelsourceids": "3460|*,410|*,427|*", "formattype": "json"}, timeout=10).json()
            for channel in list:
                if channel["Channel"]["Name"] == "TOON":
                    for program in channel["ProgramSchedules"]:
                        if skip_first:
                            skip_first = False
                            continue
                        if text.replace(' ','') != '#next' and program["Title"] != getShow(text.replace('#next ', '')):
                            continue
                        if program["TVObject"] and int(program["TVObject"]["SeasonNumber"]) != 0 and int(program["TVObject"]["EpisodeNumber"]) != 0:
                            SeasonNumber = '0' + str(program["TVObject"]["SeasonNumber"]) if int(program["TVObject"]["SeasonNumber"]) < 10 else str(program["TVObject"]["SeasonNumber"])
                            EpisodeNumber = '0' + str(program["TVObject"]["EpisodeNumber"]) if int(program["TVObject"]["EpisodeNumber"]) < 10 else str(program["TVObject"]["EpisodeNumber"])
                            EpisodeNo = 'S' + SeasonNumber + 'E' + EpisodeNumber + ' '
                        else:
                            EpisodeNo = '未知集数 '
                        message_text = '<b>' + program["Title"] + ' '
                        message_text += EpisodeNo if EpisodeNo != '未知集数 ' else ''
                        message_text += '- ' + program["EpisodeTitle"] + '</b>\n<i>即将于' + fixTime(program["StartTime"]) + '在' + channel["Channel"]["Name"] + '放送，' + program["Rating"].replace('@', '-') + '</i>\n'
                        message_text += program["CopyText"] if program["CopyText"] else '暂无简介'
                        result.append({
                            "type": "article",
                            "id": str(int(source["id"]) + int(time.time()) + len(result)),
                            "title": program["EpisodeTitle"],
                            "input_message_content": {
                                "message_text": message_text,
                                "parse_mode": 'HTML'
                            },
                            "description": program["Title"] + ' - ' + fixTime(program["StartTime"]) if text.replace(' ','') == '#next' else EpisodeNo + '- ' + fixTime(program["StartTime"]),
                            "thumb_url": getThumbnailByShow(fixShowName(program["Title"]))
                        })
                        if source["from"] == "telegram-inlinequery" and len(result) >= 5:
                            sendReply(source, result, "telegram-inlinequeryresult")
                            return
                    break
        except Exception:
            sendReply(source, ['Cathy也不知道的喵~'])
            return
        if result == []:
            result = [{
                "type": "article",
                "id": str(int(source["id"]) + int(time.time())),
                "title": "两周内没有发现TV放送的喵~",
                "input_message_content": {
                    "message_text": "两周内没有发现TV放送的喵~"
                },
                "thumb_url": getThumbnailByShow(show_name)
        }]
        sendReply(source, result, "telegram-inlinequeryresult")

def newOnAir(source, text):
    from main import sendReply, sendBusy
    if text.replace(' ','') != '#new':
        show_name = getShow(text.replace('#new ', ''))
        if show_name == 'ERROR':
            sendReply(source, ['你输入的命令好像有误的喵~'])
            return
    sendBusy(source, '稍等一下哦，Cathy去查查放送表的喵~')
    try:
        url = "https://mobilelistings.tvguide.com/Listingsweb/ws/rest/schedules/80001/start/" + str(int(time.time())) + "/duration/" + str(14*24*60)
        list = requests.get(url, params = {"channelsourceids": "3460|*,410|*,427|*", "formattype": "json"}, timeout=10).json()
        if source["from"] == "telegram-inlinequery":
            results = []
        for channel in list:
            if channel["Channel"]["Name"] == "TOON":
                for program in channel["ProgramSchedules"]:
                    if 4 == (4 & program["AiringAttrib"]):
                        if program["TVObject"] and int(program["TVObject"]["SeasonNumber"]) != 0 and int(program["TVObject"]["EpisodeNumber"]) != 0:
                            SeasonNumber = '0' + str(program["TVObject"]["SeasonNumber"]) if int(program["TVObject"]["SeasonNumber"]) < 10 else str(program["TVObject"]["SeasonNumber"])
                            EpisodeNumber = '0' + str(program["TVObject"]["EpisodeNumber"]) if int(program["TVObject"]["EpisodeNumber"]) < 10 else str(program["TVObject"]["EpisodeNumber"])
                            EpisodeNo = 'S' + SeasonNumber + 'E' + EpisodeNumber + ' '
                        else:
                            EpisodeNo = '未知集数 '
                        if text.replace(' ','') == '#new':
                            if source["from"] != "telegram-inlinequery":
                                sendReply(source, ['即将在' + channel["Channel"]["Name"] + '首播', program["Title"], '播出时间（北京时间）：', fixTime(program["StartTime"]), '这集的标题是：', program["EpisodeTitle"]])
                                return
                            else:
                                message_text = '<b>' + program["Title"] + ' '
                                message_text += EpisodeNo if EpisodeNo != '未知集数 ' else ''
                                message_text += '- ' + program["EpisodeTitle"] + '</b>\n<i>即将于' + fixTime(program["StartTime"]) + '在' + channel["Channel"]["Name"] + '首播，' + program["Rating"].replace('@', '-') + '</i>\n'
                                message_text += program["CopyText"] if program["CopyText"] else '暂无简介'
                                results.append({
                                    "type": "article",
                                    "id": str(int(source["id"]) + int(time.time()) + len(results)),
                                    "title": program["EpisodeTitle"],
                                    "input_message_content": {
                                        "message_text": message_text,
                                        "parse_mode": 'HTML'
                                    },
                                    "description": program["Title"] + ' - ' + fixTime(program["StartTime"]),
                                    "thumb_url": getThumbnailByShow(fixShowName(program["Title"]))
                                })
                        if text.replace(' ','') != '#new' and fixShowName(program["Title"]) == show_name:
                            if source["from"] != "telegram-inlinequery":
                                sendReply(source, ['下一次首播时间（北京时间）：', fixTime(program["StartTime"]), '这集的标题是：', program["EpisodeTitle"]])
                                return
                            else:
                                message_text = '<b>' + show_name + ' '
                                message_text += EpisodeNo if EpisodeNo != '未知集数 ' else ''
                                message_text += '- ' + program["EpisodeTitle"] + '</b>\n<i>即将于' + fixTime(program["StartTime"]) + '在' + channel["Channel"]["Name"] + '首播，' + program["Rating"].replace('@', '-') + '</i>\n'
                                message_text += program["CopyText"] if program["CopyText"] else '暂无简介'
                                results.append({
                                    "type": "article",
                                    "id": str(int(source["id"]) + int(time.time()) + len(results)),
                                    "title": program["EpisodeTitle"],
                                    "input_message_content": {
                                        "message_text": message_text,
                                        "parse_mode": 'HTML'
                                    },
                                    "description": EpisodeNo + '- ' + fixTime(program["StartTime"]),
                                    "thumb_url": getThumbnailByShow(show_name)
                                })
                        if source["from"] == "telegram-inlinequery" and len(results) >= 5:
                            sendReply(source, results, "telegram-inlinequeryresult")
                            return
                break
    except Exception:
        sendReply(source, ['Cathy也不知道的喵~'])
        return
    if source["from"] == "telegram-inlinequery" and results != []:
        sendReply(source, results, "telegram-inlinequeryresult")
        return
    if source["from"] == "telegram-inlinequery":
        results = [{
            "type": "article",
            "id": str(int(source["id"]) + int(time.time())),
            "title": "两周内没有发现TV首播的喵~",
            "input_message_content": {
                "message_text": "两周内没有发现TV首播的喵~"
            },
            "description": '请注意Cathy无法查询网络先行的喵~',
            "thumb_url": getThumbnailByShow(show_name)
        }]
        sendReply(source, results, "telegram-inlinequeryresult")
    else:
        sendReply(source, ['两周内没有发现TV首播的喵~'])
    return

def roomTitle(title):
    url = 'https://api.live.bilibili.com/mhand/Assistant/updateRoomInfo'
    params = {
        'access_key': getConfig('host', 'accesskey')
    }
    data = {
        'roomId': getConfig('host', 'roomid'),
        'title': title
    }
    response = bilireq(url, params=params, data=data).json()
    if response["code"] == 0:
        printlog("INFO", "Successfully changed room title to " + title)
    else:
        printlog("ERROR", "Failed to change room title to " + title + ". API says " + response["message"])

def initStream(argv):
    printlog("INFO", "I'm going to do nothing. Write some code in plugin.py please.")
