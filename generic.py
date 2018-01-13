# -*- coding: utf-8 -*-

import requests
from config import *
import datetime

def printlog(type, message):
    print "[" + type + "] " + message

def getRoomID():
    url = 'https://space.bilibili.com/ajax/live/getLive'
    params = {
        'mid': BILI_UID
    }
    return requests.get(url, params=params).json()["data"]

def convertTime(string):
    return int((datetime.datetime.strptime(string, '%Y-%m-%dT%H:%M:%SZ') - datetime.datetime(1970, 1, 1)).total_seconds())

bili_roomid = getRoomID()