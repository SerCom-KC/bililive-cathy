# -*- coding: utf-8 -*-

import requests
import sys
import time
from hashlib import md5
import traceback
import atexit

TELEGRAM_API = "https://api.telegram.org"

def printlog(log_type, message):
    log_message = '[' + str(int(time.time())) + '][' + log_type + '] ' + message
    print(log_message)
    with open(sys.path[0] + '/cathy.log', 'a') as logfile:
        logfile.write(log_message + '\n')
    if getConfig('telegram', 'token') != "" and getConfig('telegram', 'log_channel') != "":
        url = TELEGRAM_API + "/bot" + getConfig('telegram', 'token') + "/sendMessage"
        requests.get(url, params = {"chat_id": int(getConfig('telegram', 'log_channel')), "text": log_message, "disable_notification": log_type == "INFO"})

def convertTime(dt):
    if dt.tzinfo is None:
        return int(time.mktime(dt.timetuple()))
    else:
        from datetime import datetime
        import pytz
        return int((dt - datetime(1970, 1, 1, tzinfo=pytz.utc)).total_seconds())

def getConfig(section, entry=None):
    from configparser import ConfigParser
    config = ConfigParser()
    config.read(sys.path[0] + '/config.ini')
    if entry:
        return config.get(section, entry)
    return dict(config.items(section))

def setConfig(section, entry, value):
    from configparser import ConfigParser
    value = value.replace('%', '%%')
    config = ConfigParser()
    config.read(sys.path[0] + '/config.ini')
    config.set(section, entry, str(value))
    with open(sys.path[0] + '/config.ini', 'w') as configFile:
        config.write(configFile)

def getBiliCookie(user):
    url = 'https://passport.bilibili.com/api/login/sso'
    params = {
        'access_key': getConfig(user, 'accesskey')
    }
    return bilireq(url, params=params).cookies

def checkToken(user, firstrun=False):
    if firstrun:
        callback_url = 'https://sercom-kc.github.io/bililive-cathy/callback.html'
        auth_url = 'https://passport.bilibili.com/register/third.html?api=' + callback_url + '&appkey=' + getConfig('oauth', 'appkey') + '&sign=' + md5(str('api=' + callback_url + getConfig('oauth', 'appsecret')).encode('utf-8')).hexdigest()
        check_auth_url = auth_url.replace('https://passport.bilibili.com/register/third.html', 'https://passport.bilibili.com/login/app/third')
        resp = requests.get(check_auth_url, timeout=3).json()
        if resp['code'] == -1:
            printlog("ERROR", "Your appkey is invalid. Find another one!")
            raise SystemExit
        elif resp['code'] == -3:
            printlog("ERROR", "Your appsecret does not match the appkey you're using. Maybe typo?")
            raise SystemExit
        if getConfig(user, 'accesskey') == '':
            printlog("ERROR", "You must set up access key of the " + user + " account. If you don't have one, generate at " + auth_url)
            raise SystemExit
    if getConfig(user, 'expires') == '' or getConfig(user, 'uid') == '':
        url = 'https://passport.bilibili.com/api/oauth'
        params = {
            'access_key': getConfig(user, 'accesskey')
        }
        resp = bilireq(url, params=params).json()
        if resp['code'] == 0:
            setConfig(user, 'expires', resp['access_info']['expires'])
            setConfig(user, 'uid', resp['access_info']['mid'])
        else:
            printlog("ERROR", "Access key of the " + user + " account is invalid. Re-generate at " + auth_url)
            raise SystemExit
    if getConfig('host', 'roomid') == '':
        url = 'https://space.bilibili.com/ajax/live/getLive'
        params = {
            'mid': getConfig('host', 'uid')
        }
        response = requests.get(url, params=params, timeout=3).json()
        if response["status"]:
            setConfig('host', 'roomid', response["data"])
        else:
            printlog("ERROR", "Failed to get room ID of host.")
    if int(getConfig(user, 'expires')) - int(time.time()) < 15*24*60*60:
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

def bilireq(url, params={}, headers={}, cookies={}, data={}):
    from collections import OrderedDict
    headers['User-Agent'] = ''
    if 'access_key' in data: # Some APIs require access_key in POST data instead of params
        data['appkey'] = getConfig('oauth', 'appkey')
        data['ts'] = str(int(time.time()))
        data = OrderedDict(sorted(data.items(), key=lambda data:data[0]))
        prestr = '&'.join('%s=%s' % key for key in data.items())
        data['sign'] = md5(str(prestr + getConfig('oauth', 'appsecret')).encode('utf-8')).hexdigest()
    else:
        params['appkey'] = getConfig('oauth', 'appkey')
        params['ts'] = str(int(time.time()))
        params = OrderedDict(sorted(params.items(), key=lambda params:params[0]))
        prestr = '&'.join('%s=%s' % key for key in params.items())
        params['sign'] = md5(str(prestr + getConfig('oauth', 'appsecret')).encode('utf-8')).hexdigest()
    if data == {}:
        return requests.get(url, params=params, headers=headers, cookies=cookies, allow_redirects=False, timeout=3)
    else:
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        return requests.post(url, params=params, headers=headers, cookies=cookies, data=data, allow_redirects=False, timeout=3)
