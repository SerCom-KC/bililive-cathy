# -*- coding: utf-8 -*-

import requests
import sys
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
    config.read(sys.path[0] + '/config.ini')
    if entry:
        return config.get(section, entry)
    return dict(config.items(section))

def setConfig(section, entry, value):
    from ConfigParser import ConfigParser
    config = ConfigParser()
    config.read(sys.path[0] + '/config.ini')
    config.set(section, entry, value)
    with open(sys.path[0] + '/config.ini', 'wb') as configFile:
        config.write(configFile)

def checkToken(user):
    callback_url = 'https://sercom-kc.github.io/bililive-cathy/callback.html'
    auth_url = 'https://passport.bilibili.com/register/third.html?api=' + callback_url + '&appkey=' + getConfig('oauth', 'appkey') + '&sign=' + md5('api=' + callback_url + getConfig('oauth', 'appsecret')).hexdigest()
    check_auth_url = auth_url.replace('https://passport.bilibili.com/register/third.html', 'https://passport.bilibili.com/login/app/third')
    resp = requests.get(check_auth_url).json()
    if resp['code'] == -1:
        printlog("ERROR", "Your appkey is invalid. Find another one!")
        quit()
    elif resp['code'] == -3:
        printlog("ERROR", "Your appsecret does not match the appkey you're using. Maybe typo?")
        quit()
    if getConfig(user, 'accesskey') == '':
        printlog("ERROR", "You must set up access key of the " + user + " account. If you don't have one, generate at " + auth_url)
        quit()
    if getConfig(user, 'expires') != '' and int(getConfig(user, 'expires')) - int(time.time()) < 15*24*60*60:
        url = 'https://passport.bilibili.com/api/login/renewToken'
        params = {
            'access_key': getConfig(user, 'accesskey')
        }
        resp = bilireq(url, params=params).json()
        if resp['code'] == 0:
            setConfig(user, 'expires', resp['expires'])
        else:
            printlog("ERROR", "Failed to renew the access key of the " + user + " account. Re-generate manually at " + auth_url)
            quit()
    url = 'https://passport.bilibili.com/api/oauth'
    params = {
        'access_key': getConfig(user, 'accesskey')
    }
    resp = bilireq(url, params=params).json()
    if resp['code'] == 0:
        setConfig(user, 'expires', resp['access_info']['expires'])
        setConfig(user, 'uid', resp['access_info']['mid'])
        url = 'https://passport.bilibili.com/api/login/sso'
        params = {
            'access_key': getConfig(user, 'accesskey')
        }
        bili_cookie[user] = bilireq(url, params=params).cookies
    else:
        printlog("ERROR", "Access key of the " + user + " account is invalid. Re-generate at " + auth_url)
        quit()

def bilireq(url, params={}, headers={}, cookies={}, data={}):
    from collections import OrderedDict
    headers['User-Agent'] = ''
    if 'access_key' in data: # Some APIs require access_key in POST data instead of params
        data['appkey'] = getConfig('oauth', 'appkey')
        data['ts'] = str(int(time.time()))
        data = OrderedDict(sorted(data.items(), key=lambda data:data[0]))
        prestr = '&'.join('%s=%s' % key for key in data.iteritems())
        data['sign'] = md5(prestr + getConfig('oauth', 'appsecret')).hexdigest()
    else:
        params['appkey'] = getConfig('oauth', 'appkey')
        params['ts'] = str(int(time.time()))
        params = OrderedDict(sorted(params.items(), key=lambda params:params[0]))
        prestr = '&'.join('%s=%s' % key for key in params.iteritems())
        params['sign'] = md5(prestr + getConfig('oauth', 'appsecret')).hexdigest()
    if data == {}:
        return requests.get(url, params=params, headers=headers, cookies=cookies, allow_redirects=False)
    else:
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        return requests.post(url, params=params, headers=headers, cookies=cookies, data=data, allow_redirects=False)

bili_roomid = getRoomID()
bili_cookie = {}
