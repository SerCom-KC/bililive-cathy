# -*- coding: utf-8 -*-

import requests
from config import *
import time

def printlog(type, message):
    print "[" + type + "] " + message

def getRoomID():
    url = 'https://space.bilibili.com/ajax/live/getLive'
    params = {
        'mid': BILI_UID
    }
    return requests.get(url, params=params).json()["data"]

def convertTime(dt):
    if dt.tzinfo is None:
        return int(time.mktime(dt.timetuple()))
    else:
        from datetime import datetime
        import pytz
        return int((dt - datetime(1970, 1, 1, tzinfo=pytz.utc)).total_seconds())

bili_roomid = getRoomID()