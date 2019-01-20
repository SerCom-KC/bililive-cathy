# -*- coding: utf-8 -*-
from generic import *
import os
import time
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
    {"showId": "444772", "shortcode": "aao"},
    {"showId": "399692", "shortcode": "su"},
    {"showId": "425772", "shortcode": "ppg2016"},
    {"showId": "423572", "shortcode": "mm"}
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
    elif text.find('字幕') != -1 and source["from"] == "bili-danmaku":
        sendReply(source, ['本直播间就是无字幕生肉放送的喵！！'])
    elif text == '#help':
        if source["from"] == "bili-danmaku":
            sendReply(source, ['呜喵~太多了不能在弹幕里发的喵！', '请在私信里发送这个命令的喵！'])
        elif source["from"] == "mastodon":
            sendReply(source, ['请直接查看置顶嘟文的喵：https://sckc.stream/@bililive_cathy_bot/100184533673968102'])
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
                '',
                '#new',
                '如果你想知道自己想看的剧什么时候更新的话，请使用这个命令喵~',
                '同样也需要在后面加上这个剧的缩写，比如 #new su 这样的喵~',
                '请注意这个命令查到的都是TV首播，也就是说如果有网络首播的话这个命令是查不到的喵~',
                '如果不指定是哪个剧的话，将会返回CARTOON NETWORK/[adult swim]接下来要TV首播的内容喵~',
                '支持的缩写列表请发送 #help list 查看的喵~'
            ]
            if source["from"] == "telegram-inlinequery" or source["from"] == "telegram-private":
                responses.extend((
                    '',
                    '使用Telegram的小伙伴还可以在与我的私聊中使用 / 作为命令开头的喵~',
                    '同时也可以在任意对话中使用inline模式唤起我的喵~不过这种情况还是只能用 # 作为命令开头的喵~',
                    '此外目前在inline模式中使用#next或#new命令的话，我可以一次性返回最多50个结果的喵~',
                    '点击结果还可以显示更多信息的喵~来试试吧喵~'
                ))
            sendReply(source, responses)
    elif text == '#help list':
        if source["from"] == "bili-danmaku":
            sendReply(source, ['呜喵~太多了不能在弹幕里发的喵！', '请在私信里发送这个命令的喵！'])
        elif source["from"] == "mastodon":
            sendReply(source, ['因为列表可能过长，所以Cathy在Mastodon上暂时不支持这个命令喵TAT'])
        else:
            reply = ['当前支持的缩写列表：']
            for show in shows_shortcode:
                reply.append(show["shortcode"] + ' - ' + getShow(show["shortcode"]))
            reply.append('如果你想看的CN或[as]番不在这个列表里的话，请联系 @SerCom_KC 追加的喵~')
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
    if show_name == "Dragon Ball Z Kai: The Final Chapters":
        show_name = "Dragon Ball Z Kai"
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

def fixEpisodeName(episode_name, force_the=False):
    for title in episode_name.split('/'):
        fixed = re.sub(r'(.*?) $', 'The \\1', title)
        fixed = re.sub(r'(.*?), The$', 'The \\1', fixed)
        if force_the and not fixed.startswith("The "):
            fixed = "The " + fixed
        else:
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

def getTVGuideEpisodeNo(program):
    if program["TVObject"] and int(program["TVObject"]["SeasonNumber"]) != 0 and int(program["TVObject"]["EpisodeNumber"]) != 0:
        SeasonNumber = "0" + str(program["TVObject"]["SeasonNumber"]) if int(program["TVObject"]["SeasonNumber"]) < 10 else str(program["TVObject"]["SeasonNumber"])
        EpisodeNumber = "0" + str(program["TVObject"]["EpisodeNumber"]) if int(program["TVObject"]["EpisodeNumber"]) < 10 else str(program["TVObject"]["EpisodeNumber"])
        EpisodeNo = "S" + SeasonNumber + "E" + EpisodeNumber
    else:
        EpisodeNo = ""
    return EpisodeNo

def getSchedule(source=None, channel='undefined', forceupdate=False):
    from main import sendBusy
    now_last_query = {'title': getConfig('extras', 'now_title'), 'episodeName': getConfig('extras', 'now_episodeName'), 'airtime': int(getConfig('extras', 'now_airtime'))}
    next_last_query = {'title': getConfig('extras', 'next_title'), 'episodeName': getConfig('extras', 'next_episodeName'), 'airtime': int(getConfig('extras', 'next_airtime'))}
    if now_last_query['title'] != '' and next_last_query['title'] != '' and int(time.time()) < next_last_query['airtime'] and not forceupdate: # needs update
        return True
    if source:
        sendBusy(source, '稍等一下哦，Cathy去查查放送表的喵~')
    try:
        if channel == 'cn' or channel == 'as' or getChannel() == 'cn' or getChannel() == 'as' or getChannel() == "restrict":
            schedule = getTVGuide(source=source, channel="TOON")
            for channel in schedule:
                if channel["Channel"]["Name"] == "TOON":
                    now_program = channel["ProgramSchedules"][0]
                    next_program = channel["ProgramSchedules"][1]
                    break
            setConfig("extras", "now_title", now_program["Title"] + " " + getTVGuideEpisodeNo(now_program))
            setConfig("extras", "now_episodeName", now_program["EpisodeTitle"])
            setConfig("extras", "now_airtime", int(now_program["StartTime"]))
            setConfig("extras", "next_title", next_program["Title"] + " " + getTVGuideEpisodeNo(next_program))
            setConfig("extras", "next_episodeName", next_program["EpisodeTitle"])
            setConfig("extras", "next_airtime", int(next_program["StartTime"]))
        elif channel == 'cnstream' or getChannel() == 'cnstream':
            resp = requests.get("https://cms-api.cartoonnetwork.com/live-stream", timeout=3).json()
            setConfig('extras', 'now_title', resp[0]["seriesName"])
            setConfig('extras', 'now_episodeName', resp[0]["episodeName"])
            setConfig('extras', 'now_airtime', int(resp[0]["time"]/1000))
            setConfig('extras', 'next_title', resp[1]["seriesName"])
            setConfig('extras', 'next_episodeName', resp[1]["episodeName"])
            setConfig('extras', 'next_airtime', int(resp[1]["time"]/1000))
        else:
            return False
        printlog("INFO", "Now on air: " + getConfig("extras", "now_title") + " - " + getConfig("extras", "now_episodeName"))
        roomNews("现在（%s）：%s\n接下来（%s）：%s" % (fixTime(getConfig("extras", "now_airtime")), getConfig("extras", "now_title"), fixTime(getConfig("extras", "next_airtime")), getConfig("extras", "next_title")))
        return True
    except Exception:
        return False

def nowOnAir(source):
    from main import sendReply
    if not getSchedule(source):
        sendReply(source, ['Cathy也不知道的喵~'])
        return
    if source["from"] != "telegram-inlinequery":
        now_last_query = {"title": getConfig("extras", "now_title"), "episodeName": getConfig("extras", "now_episodeName"), "airtime": int(getConfig("extras", "now_airtime"))}
        result = ["正在播出的是："]
        result.append(now_last_query["title"])
        if now_last_query["episodeName"] != None and now_last_query["episodeName"] != "":
            result.append("这集的标题是：")
            result.append(now_last_query["episodeName"])
        sendReply(source, result)
    else:
        try:
            schedule = getTVGuide(source=source, channel="TOON")
            for channel in schedule:
                if channel["Channel"]["Name"] == "TOON":
                    program = channel["ProgramSchedules"][0]
            EpisodeNo = getTVGuideEpisodeNo(program)
        except Exception:
            sendReply(source, ["Cathy也不知道的喵~"])
            return
        if EpisodeNo == "": EpisodeNo = "未知集数 "
        else: EpisodeNo += " "
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

def nextOnAir(source, text):
    from main import sendReply
    show_name = getShow(text.replace("#next ", ""))
    if source["from"] != "telegram-inlinequery" and text.replace(" ","") != "#next":
        try:
            schedule = getTVGuide(source=source, channel="TOON")
            for channel in schedule:
                if channel["Channel"]["Name"] == "TOON":
                    break
        except Exception:
            sendReply(source, ["Cathy也不知道的喵~"])
            return
    if source["from"] != "telegram-inlinequery":
        if text.replace(" ","") == "#next":
            next_last_query = {"title": getConfig("extras", "next_title"), "episodeName": getConfig("extras", "next_episodeName"), "airtime": int(getConfig("extras", "next_airtime"))}
            result = ["接下来播出的是："]
            result.append(next_last_query["title"])
            if next_last_query["episodeName"] != None and next_last_query["episodeName"] != "":
                result.append("这集的标题是：")
                result.append(next_last_query["episodeName"])
            sendReply(source, result)
        else:
            show_id = getShowID(text.replace("#next ", ""))
            if show_id == "ERROR":
                sendReply(source, ["你输入的命令好像有误的喵~"])
                return
            skip = True
            query_program = None
            for program in channel["ProgramSchedules"]:
                if skip:
                    skip = False
                    continue
                if program["Title"] == show_name:
                    query_program = program
                    break
            #sendReply(source, ["这个功能被禁用了，非常抱歉呜喵QAQ"])
            #return
            if query_program:
                sendReply(source, ["下一次播出时间（东八区）：", fixTime(int(program["StartTime"])), "这集的标题是：", getTVGuideEpisodeNo(program) + " " + program["EpisodeTitle"]])
            else:
                result = ["在可预见的未来没有发现放送的喵~"]
                if show_name == "ERROR":
                    result.append("也许是你输错了数字ID喵？")
                sendReply(source, result)
    else:
        result = []
        skip_first = True
        try:
            if text.replace(' ','') != '#next' and show_name == 'ERROR':
                sendReply(source, ['你输入的命令好像有误的喵~'])
            else:
                for program in channel["ProgramSchedules"]:
                    if skip_first:
                        skip_first = False
                        continue
                    if text.replace(' ','') != '#next' and program["Title"] != show_name:
                        continue
                    EpisodeNo = getTVGuideEpisodeNo(program)
                    if EpisodeNo == "": EpisodeNo = "未知集数 "
                    else: EpisodeNo += " "
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
                    if len(result) >= 50:
                        sendReply(source, result, "telegram-inlinequeryresult")
                        return
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
                        if int(time.time()) > program["StartTime"]:
                            continue
                        if program["TVObject"] and int(program["TVObject"]["SeasonNumber"]) != 0 and int(program["TVObject"]["EpisodeNumber"]) != 0:
                            SeasonNumber = '0' + str(program["TVObject"]["SeasonNumber"]) if int(program["TVObject"]["SeasonNumber"]) < 10 else str(program["TVObject"]["SeasonNumber"])
                            EpisodeNumber = '0' + str(program["TVObject"]["EpisodeNumber"]) if int(program["TVObject"]["EpisodeNumber"]) < 10 else str(program["TVObject"]["EpisodeNumber"])
                            EpisodeNo = 'S' + SeasonNumber + 'E' + EpisodeNumber + ' '
                        else:
                            EpisodeNo = '未知集数 '
                        if text.replace(' ','') == '#new':
                            if source["from"] != "telegram-inlinequery":
                                sendReply(source, ['即将在' + channel["Channel"]["Name"] + '首播', program["Title"], '播出时间（东八区）：', fixTime(program["StartTime"]), '这集的标题是：', getTVGuideEpisodeNo(program) + " " + program["EpisodeTitle"]])
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
                                sendReply(source, ['下一次首播时间（东八区）：', fixTime(program["StartTime"]), '这集的标题是：', getTVGuideEpisodeNo(program) + " " + program["EpisodeTitle"]])
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
    url = "https://api.live.bilibili.com/room/v1/Room/update"
    params = {
        "access_key": getConfig("host", "accesskey")
    }
    data = {
        "room_id": getConfig("host", "roomid"),
        "title": title
    }
    response = bilireq(url, params=params, data=data).json()
    if response["code"] == 0:
        printlog("INFO", "Successfully changed room title to " + title)
    else:
        printlog("ERROR", "Failed to change room title to " + title + ". API says " + response["message"])

def roomNews(content):
    url = "https://api.live.bilibili.com/room_ex/v1/RoomNews/update"
    params = {
        "access_key": getConfig("host", "accesskey")
    }
    data = {
        "roomid": getConfig("host", "roomid"),
        "uid": getConfig("host", "uid"),
        "content": content
    }
    response = bilireq(url, params=params, data=data).json()
    if response["code"] == 0:
        printlog("INFO", "Successfully changed room announcement to %s" % (content))
    else:
        printlog("ERROR", "Failed to change room announcement to %s. API says %s" % (content, response["message"]))

def initStream(argv):
    printlog("INFO", "I'm going to do nothing. Write some code in plugin.py please.")
