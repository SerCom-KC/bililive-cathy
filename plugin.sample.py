# -*- coding: utf-8 -*-
from generic import *
import os
import time
from lxml import etree
from datetime import datetime, timedelta
import pytz
import re

tvguide_list = []

shows_shortcode = [
    {"showId": "376453", "shortcode": "tawog"},
    {"showId": "403152", "shortcode": "cl"},
    {"showId": "393474", "shortcode": "ttg"},
    {"showId": "326561", "shortcode": "tt"},
    {"showId": "442472", "shortcode": "uni"},
    {"showId": "368594", "shortcode": "at"},
    {"showId": "438472", "shortcode": "ben10"},
    {"showId": "419032", "shortcode": "wbb"},
    {"showId": "440832", "shortcode": "okko"},
    {"showId": "444812", "shortcode": "fs"},
    {"showId": "444772", "shortcode": "aao"},
    {"showId": "399692", "shortcode": "su"},
    {"showId": "425772", "shortcode": "ppg2016"},
    {"showId": "447432", "shortcode": "flcl"},
    {"showId": "401312", "shortcode": "ram"},
    {"showId": "398292", "shortcode": "mp"},
    {"showId": "423572", "shortcode": "mm"},
    {"showId": "331864", "shortcode": "rc"},
    {"showId": "447434", "shortcode": "flclpro"}
]

def isAdmin(source):
    if (source["from"] == "bili-danmaku" or source["from"] == "bili-msg"):
        if str(source["uid"]) == getConfig('host', 'uid'):
            return True
        else:
            return False
    elif (source["from"] == "telegram-private" or source["from"] == "telegram-inlinequery"):
        for id in getConfig('telegram', 'admins').split('|'):
            if source["user"]["id"] == int(id):
                return True
        return False
    else:
        return False

def commandParse(source, text):
    from main import sendReply
    if text == '#status':
        if isAdmin(source):
            sendReply(source, ['Cathy运行时间：' + str(timedelta(seconds=int(time.time()) - int(getConfig('extras', 'start_time'))))])
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
                    '同时也可以在任意对话中使用inline模式唤起我的喵~不过这种情况还是只能用 # 作为命令开头，并且完全使用第三方（TV Guide）数据源的喵~',
                    '此外目前在inline模式中使用#next或#new命令的话，我可以一次性返回最多50个结果的喵~',
                    '点击结果还可以显示更多信息的喵~来试试吧喵~'
                ))
            sendReply(source, responses)
    elif text == '#help list':
        if source["from"] == "bili-danmaku":
            sendReply(source, ['呜喵~太多了不能在弹幕里发的喵！', '请在私信里发送这个命令的喵！'])
        else:
            reply = ['当前支持的缩写列表：']
            for show in shows_shortcode:
                reply.append(show["shortcode"] + ' - ' + getShow(show["shortcode"]))
            reply.append('如果你想看的特纳剧不在这个列表里的话，请联系 @SerCom_KC 追加的喵~')
            sendReply(source, reply)
    else:
        return False
    return True

def getShow(id):
    id = id.lower()
    if not id.isdigit():
        for show in shows_shortcode:
        if id == show["shortcode"]:
            id = show["showId"]
    if id.isdigit():
        url = "https://raw.githubusercontent.com/SerCom-KC/cartoon-network-schedule/master/show-list?"
        shows = requests.get(url, timeout=3).json()
        for show in shows:
            if show["showId"] == id:
                return show["title"]
    return "ERROR"

def getShowID(id):
    id = id.lower()
    if id.isdigit():
        return id
    for show in shows_shortcode:
        if id == show["shortcode"]:
            return show["showId"]
    return "ERROR"

def getThumbnailByShow(show_name):
    url = "https://raw.githubusercontent.com/SerCom-KC/cartoon-network-schedule/master/show-list?"
    shows = requests.get(url, timeout=3).json()
    for show in shows:
        if show["title"] == show_name:
            return show["thumbnail"]
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

def getTVGuide(source=None, channel=None):
    global tvguide_list
    needs_update = False
    if tvguide_list != []:
        for tvguide_channel in tvguide_list:
            if int(time.time()) > int(tvguide_channel["ProgramSchedules"][0]["EndTime"]): # Does any program presented in the list has finished airing?
                needs_update = True
                break
    else: # Or the list is empty?
        needs_update = True
    if needs_update:
        if source: # Send a busy status if this request is fired by human
            from main import sendBusy
            sendBusy(source, '稍等一下哦，Cathy去查查放送表的喵~')
        url = "https://mobilelistings.tvguide.com/Listingsweb/ws/rest/schedules/80001/start/" + str(int(time.time())) + "/duration/" + str(14*24*60)
        tvguide_list = requests.get(url, params = {"channelsourceids": "3460|*,410|*,427|*", "formattype": "json"}, timeout=10).json()
    if channel == None:
        return tvguide_list
    for tvguide_channel in tvguide_list:
        if tvguide_channel["Channel"]["Name"] == channel:
            return [tvguide_channel]
    return []

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
        if allshows[index].xpath('@urlName')[0] == "Cartoon Network":
            title_fixed = getShow(allshows[index].xpath('@showId')[0])
            if title_fixed == 'ERROR': # ID not in our database yet
                title_fixed = "（欸，是叫什么来着喵？）"
            setConfig('extras', 'next_title', title_fixed)
        else:
            setConfig('extras', 'next_title', fixShowName(allshows[index].xpath('@urlName')[0]))
        # fetch episodeName manually to avoid "The" problem in https://gitlab.com/ctoon/cn-schedule-fetcher/issues/1 since getEpisodeDesc returns standard ", The"
        url = 'https://www.adultswim.com/adultswimdynsched/xmlServices/ScheduleServices'
        params = {
            'methodName': 'getEpisodeDesc',
            'showId': allshows[index].xpath('@showId')[0],
            'episodeId': allshows[index].xpath('@episodeId')[0],
            'isFeatured': 'N' #allshows[index].xpath('@isFeatured')[0]
        }
        episodeName = etree.XML(requests.get(url, params=params, timeout=3).content).xpath("//Desc/episodeDesc/text()")[0]
        if episodeName[-1] == ' ':
            episodeName = episodeName[:-1]
        setConfig('extras', 'next_episodeName', fixEpisodeName(episodeName))
        setConfig('extras', 'next_airtime', convertTime(show_time))
        # update now_last_query
        if prev_show != '':
            show = prev_show
        else:
            show = allshows[index-1]
        date_str = show.xpath('@date')[0] + ' ' + show.xpath('@military')[0]
        show_time = pytz.timezone('US/Eastern').localize(datetime.strptime(date_str, '%m/%d/%Y %H:%M'))
        if show.xpath('@urlName')[0] == "Cartoon Network":
            title_fixed = getShow(show.xpath('@showId')[0])
            if title_fixed == 'ERROR': # ID not in our database yet
                title_fixed = "（欸，是叫什么来着喵？）"
            setConfig('extras', 'now_title', title_fixed)
        else:
            setConfig('extras', 'now_title', fixShowName(show.xpath('@urlName')[0]))
        # fetch episodeName manually to avoid "The" problem in https://gitlab.com/ctoon/cn-schedule-fetcher/issues/1 since getEpisodeDesc returns standard ", The"
        url = 'https://www.adultswim.com/adultswimdynsched/xmlServices/ScheduleServices'
        params = {
            'methodName': 'getEpisodeDesc',
            'showId': show.xpath('@showId')[0],
            'episodeId': show.xpath('@episodeId')[0],
            'isFeatured': 'N' #show.xpath('@isFeatured')[0]
        }
        episodeName = etree.XML(requests.get(url, params=params, timeout=3).content).xpath("//Desc/episodeDesc/text()")[0]
        if episodeName[-1] == ' ':
            episodeName = episodeName[:-1]
        setConfig('extras', 'now_episodeName', fixEpisodeName(episodeName))
        setConfig('extras', 'now_airtime', convertTime(show_time))
        printlog("INFO", "Now on air: " + getConfig('extras', 'now_title') + ' - ' + getConfig('extras', 'now_episodeName'))
        return True
    return False

def getSchedule(source=None, channel='undefined'):
    from main import sendBusy
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
        sendReply(source, result)
    else:
        try:
            schedule = getTVGuide(source=source, channel="TOON")
            for channel in schedule:
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
                    if program["EpisodeTitle"] != '':
                        message_text += '- ' + program["EpisodeTitle"]
                    message_text += '</b>\n<i>当前正在' + channel["Channel"]["Name"] + '放送中，' + fixTime(program["StartTime"]) + '-' + fixTime(program["EndTime"]) + '，' + program["Rating"].replace('@', '-') + '</i>\n'
                    message_text += program["CopyText"] if program["CopyText"] else '暂无简介'
                    if program["EpisodeTitle"] != '':
                        description = program["Title"] + ' - ' + fixTime(program["StartTime"])
                    else:
                        description = fixTime(program["StartTime"])
                    result = [{
                        "type": "article",
                        "id": str(int(source["id"]) + int(time.time())),
                        "title": program["EpisodeTitle"] if program["EpisodeTitle"] != '' else program["Title"],
                        "input_message_content": {
                            "message_text": message_text,
                            "parse_mode": 'HTML'
                        },
                        "description": description,
                        "thumb_url": getThumbnailByShow(fixShowName(program["Title"]))
                    }]
                    sendReply(source, result, "telegram-inlinequeryresult")
                    return
        except Exception:
            pass
        sendReply(source, ['Cathy也不知道的喵~'])
        return
    

def nextOnAir(source, text):
    from main import sendReply
    show_name = getShow(text.replace('#next ', ''))
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
                if show_name == 'ERROR':
                    result.append('也许是你输错了数字ID喵？')
                sendReply(source, result)
            return
    else:
        result = []
        skip_first = True
        try:
            if text.replace(' ','') != '#next' and show_name == 'ERROR':
                sendReply(source, ['你输入的命令好像有误的喵~'])
                return
            schedule = getTVGuide(source=source, channel="TOON")
            for channel in schedule:
                if channel["Channel"]["Name"] == "TOON":
                    for program in channel["ProgramSchedules"]:
                        if skip_first:
                            skip_first = False
                            continue
                        if text.replace(' ','') != '#next' and program["Title"] != show_name:
                            continue
                        if program["TVObject"] and int(program["TVObject"]["SeasonNumber"]) != 0 and int(program["TVObject"]["EpisodeNumber"]) != 0:
                            SeasonNumber = '0' + str(program["TVObject"]["SeasonNumber"]) if int(program["TVObject"]["SeasonNumber"]) < 10 else str(program["TVObject"]["SeasonNumber"])
                            EpisodeNumber = '0' + str(program["TVObject"]["EpisodeNumber"]) if int(program["TVObject"]["EpisodeNumber"]) < 10 else str(program["TVObject"]["EpisodeNumber"])
                            EpisodeNo = 'S' + SeasonNumber + 'E' + EpisodeNumber + ' '
                        else:
                            EpisodeNo = '未知集数 '
                        message_text = '<b>' + program["Title"] + ' '
                        message_text += EpisodeNo if EpisodeNo != '未知集数 ' else ''
                        if program["EpisodeTitle"] != '':
                            message_text += '- ' + program["EpisodeTitle"]
                        message_text += '</b>\n<i>即将于' + fixTime(program["StartTime"]) + '在' + channel["Channel"]["Name"] + '放送，' + program["Rating"].replace('@', '-') + '</i>\n'
                        message_text += program["CopyText"] if program["CopyText"] else '暂无简介'
                        if text.replace(' ','') == '#next':
                            if program["EpisodeTitle"] != '':
                                description = program["Title"] + ' - ' + fixTime(program["StartTime"])
                            else:
                                description = fixTime(program["StartTime"])
                        else:
                            description = EpisodeNo + '- ' + fixTime(program["StartTime"])
                        result.append({
                            "type": "article",
                            "id": str(int(source["id"]) + int(time.time()) + len(result)),
                            "title": program["EpisodeTitle"] if program["EpisodeTitle"] != '' else program["Title"],
                            "input_message_content": {
                                "message_text": message_text,
                                "parse_mode": 'HTML'
                            },
                            "description": description,
                            "thumb_url": getThumbnailByShow(fixShowName(program["Title"]))
                        })
                        if source["from"] == "telegram-inlinequery" and len(result) >= 50:
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
            if text.replace('#next ', '').isdigit():
                result[0]["description"] = "也许是你输入的数字ID暂时与第三方数据对不上的喵~"
        sendReply(source, result, "telegram-inlinequeryresult")

def newOnAir(source, text):
    from main import sendReply
    show_name = ""
    if text.replace(' ','') != '#new':
        show_name = getShow(text.replace('#new ', ''))
        if show_name == 'ERROR':
            sendReply(source, ['你输入的命令好像有误的喵~'])
            return
    try:
        schedule = getTVGuide(source=source, channel="TOON")
        if source["from"] == "telegram-inlinequery":
            results = []
        for channel in schedule:
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
                                if program["EpisodeTitle"] != '':
                                    message_text += '- ' + program["EpisodeTitle"]
                                message_text += '</b>\n<i>即将于' + fixTime(program["StartTime"]) + '在' + channel["Channel"]["Name"] + '首播，' + program["Rating"].replace('@', '-') + '</i>\n'
                                message_text += program["CopyText"] if program["CopyText"] else '暂无简介'
                                if program["EpisodeTitle"] != '':
                                    description = program["Title"] + ' - ' + fixTime(program["StartTime"])
                                else:
                                    description = fixTime(program["StartTime"])
                                results.append({
                                    "type": "article",
                                    "id": str(int(source["id"]) + int(time.time()) + len(results)),
                                    "title": program["EpisodeTitle"] if program["EpisodeTitle"] != '' else program["Title"],
                                    "input_message_content": {
                                        "message_text": message_text,
                                        "parse_mode": 'HTML'
                                    },
                                    "description": description,
                                    "thumb_url": getThumbnailByShow(fixShowName(program["Title"]))
                                })
                        elif text.replace(' ','') != '#new' and fixShowName(program["Title"]) == show_name:
                            if source["from"] != "telegram-inlinequery":
                                sendReply(source, ['下一次首播时间（北京时间）：', fixTime(program["StartTime"]), '这集的标题是：', program["EpisodeTitle"]])
                                return
                            else:
                                message_text = '<b>' + show_name + ' '
                                message_text += EpisodeNo if EpisodeNo != '未知集数 ' else ''
                                if program["EpisodeTitle"] != '':
                                    message_text += '- ' + program["EpisodeTitle"]
                                message_text += '</b>\n<i>即将于' + fixTime(program["StartTime"]) + '在' + channel["Channel"]["Name"] + '首播，' + program["Rating"].replace('@', '-') + '</i>\n'
                                message_text += program["CopyText"] if program["CopyText"] else '暂无简介'
                                results.append({
                                    "type": "article",
                                    "id": str(int(source["id"]) + int(time.time()) + len(results)),
                                    "title": program["EpisodeTitle"] if program["EpisodeTitle"] != '' else program["Title"],
                                    "input_message_content": {
                                        "message_text": message_text,
                                        "parse_mode": 'HTML'
                                    },
                                    "description": EpisodeNo + '- ' + fixTime(program["StartTime"]),
                                    "thumb_url": getThumbnailByShow(show_name)
                                })
                        if source["from"] == "telegram-inlinequery" and len(results) >= 50:
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
