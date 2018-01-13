# -*- coding: utf-8 -*-
from generic import *
import os

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