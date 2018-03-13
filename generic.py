# -*- coding: utf-8 -*-

import requests

import time
from hashlib import md5

def printlog(type, message):
    print "[" + type + "] " + message

def getRoomID():
    url = 'https://space.bilibili.com/ajax/live/getLive'
    params = {
        'mid': getConfig('host', 'uid')
    }
    return requests.get(url, params=params).json()["data"]

def convertTime(dt):
    if dt.tzinfo is None:
        return int(time.mktime(dt.timetuple()))
    else:
        from datetime import datetime
        import pytz
        return int((dt - datetime(1970, 1, 1, tzinfo=pytz.utc)).total_seconds())

def getConfig(section, entry=None):
    from ConfigParser import ConfigParser
    config = ConfigParser()
    config.read(__file__.replace('generic.pyc', '').replace('generic.py', '') + 'config.ini')
    if entry:
        return config.get(section, entry)
    return dict(config.items(section))

def setConfig(section, entry, value):
    from ConfigParser import ConfigParser
    config = ConfigParser()
    config.read(__file__.replace('generic.pyc', '').replace('generic.py', '') + 'config.ini')
    config.set(section, entry, value)
    with open(__file__.replace('generic.pyc', '').replace('generic.py', '') + 'config.ini', 'wb') as configFile:
        config.write(configFile)

def bilireq(url, params={}, headers={}, cookies={}, data={}):
    from collections import OrderedDict
    params['appkey'] = getConfig('oauth', 'appkey')
    params['ts'] = str(int(time.time()))
    params = OrderedDict(sorted(params.items(), key=lambda params:params[0]))
    prestr = '&'.join('%s=%s' % key for key in params.iteritems())
    params['sign'] = md5(prestr + getConfig('oauth', 'appsecret')).hexdigest()
    if data == {}:
        return requests.get(url, params=params, headers=headers, cookies=cookies, allow_redirects=False)
    else:
        return requests.post(url, params=params, headers=headers, cookies=cookies, data=data, allow_redirects=False)

bili_roomid = getRoomID()
bili_cookie = {}