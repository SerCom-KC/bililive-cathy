# -*- coding: utf-8 -*-

import requests
import sys
import time
from hashlib import md5
import traceback
import atexit

TELEGRAM_API = "https://api.telegram.org"

def printlog(log_type, message):
    log_message = '[' + str(int(time.time())) + '] [' + log_type + '] ' + message
    print(log_message)
    with open(sys.path[0] + '/cathy.log', 'a', encoding='utf-8') as logfile:
        logfile.write(log_message + '\n')
    if getConfig('telegram', 'token') != "" and getConfig('telegram', 'log_channel') != "":
        url = TELEGRAM_API + "/bot" + getConfig('telegram', 'token') + "/sendMessage"
        requests.get(url, params = {"chat_id": int(getConfig('telegram', 'log_channel')), "text": log_message, "disable_notification": log_type != "ERROR"})

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
    config.read(sys.path[0] + '/config.ini', encoding="utf-8")
    if entry:
        return config.get(section, entry)
    return dict(config.items(section))

def setConfig(section, entry, value):
    from configparser import ConfigParser
    value = str(value).replace('%', '%%')
    config = ConfigParser()
    config.read(sys.path[0] + '/config.ini')
    config.set(section, entry, str(value))
    with open(sys.path[0] + '/config.ini', 'w', encoding='utf-8') as configFile:
        config.write(configFile)

def getBiliCookie(user):
    from collections import OrderedDict
    url = "https://passport.bilibili.com/api/login/sso"
    params = {
        "appkey": getConfig("oauth", "appkey"),
        "access_key": getConfig(user, "accesskey"),
        "ts": str(int(time.time()))
    }
    params = OrderedDict(sorted(params.items(), key=lambda params:params[0]))
    prestr = '&'.join('%s=%s' % key for key in params.items())
    params['sign'] = md5(str(prestr + getConfig('oauth', 'appsecret')).encode('utf-8')).hexdigest()
    resp = requests.get(url, params=params, allow_redirects=False, timeout=3)
    return resp.cookies

def login(user):
    from Crypto.PublicKey import RSA
    from Crypto.Cipher import PKCS1_v1_5
    from base64 import b64encode
    flag = False
    try:
        username = getConfig(user, "username")
        password = getConfig(user, "password")
    except Exception:
        flag = True
    if not flag and (username == "" or password == ""):
        flag = True
    if flag:
        printlog("ERROR", "You didn't set up username/password of the %s account in your config file." % (user))
        raise SystemExit
    resp = bilireq("https://passport.bilibili.com/api/oauth2/getKey").json()
    if resp["code"] != 0:
        printlog("ERROR", "Failed to get bilibili's RSA public key. Please check your appkey/appsecret.")
        raise SystemExit
    key = resp["data"]
    encryptor = PKCS1_v1_5.new(RSA.importKey(bytes(key["key"], "utf-8")))
    password = str(b64encode(encryptor.encrypt(bytes(key["hash"] + password, "utf-8"))), "utf-8")
    username = username.replace("/", "%2F").replace("=", "%3D").replace("@", "%40").replace("+", "%2B")
    password = password.replace("/", "%2F").replace("=", "%3D").replace("@", "%40").replace("+", "%2B")
    resp = bilireq("https://passport.bilibili.com/api/v2/oauth2/login", data={"username": username, "password": password}, no_urlencode=True).json()
    if resp["code"] == -105:
        printlog("ERROR", "bilibili is requiring a CAPTCHA challenge. Please try again later.")
    elif resp["code"] != 0:
        printlog("ERROR", "Failed to sign in to account %s with username/password. Please check your config file." % (user))
    setConfig(user, "expires", resp["ts"] + resp["data"]["token_info"]["expires_in"])
    setConfig(user, "uid", resp["data"]["token_info"]["mid"])
    setConfig(user, "accesskey", resp["data"]["token_info"]["access_token"])
    setConfig(user, "refreshtoken", resp["data"]["token_info"]["refresh_token"])

def checkToken(user, firstrun=False):
    third_login = True
    if firstrun:
        callback_url = 'https://sercom-kc.github.io/bililive-cathy/callback.html'
        auth_url = 'https://passport.bilibili.com/register/third.html?api=' + callback_url + '&appkey=' + getConfig('oauth', 'appkey') + '&sign=' + md5(str('api=' + callback_url + getConfig('oauth', 'appsecret')).encode('utf-8')).hexdigest()
        check_auth_url = auth_url.replace('https://passport.bilibili.com/register/third.html', 'https://passport.bilibili.com/login/app/third')
        resp = requests.get(check_auth_url, timeout=3).json()
        if resp["data"] == -400:
            printlog("WARNING", "Cannot verify your appkey at the moment. Will try to proceed anyway.")
            third_login = False
        elif resp['code'] == -1:
            printlog("ERROR", "Your appkey is invalid. Find another one!")
            raise SystemExit
        elif resp['code'] == -3:
            printlog("ERROR", "Your appsecret does not match the appkey you're using. Maybe typo?")
            raise SystemExit
        if getConfig(user, 'accesskey') == '':
            printlog("ERROR", "Access key of the %s account is missing. Will try to sign in with username/password." % (user))
            login(user)
    if firstrun or getConfig(user, 'expires') == '' or getConfig(user, 'uid') == '':
        url = 'https://passport.bilibili.com/api/oauth'
        params = {
            'access_key': getConfig(user, 'accesskey')
        }
        resp = bilireq(url, params=params).json()
        if resp['code'] == 0:
            setConfig(user, 'expires', resp['access_info']['expires'])
            setConfig(user, 'uid', resp['access_info']['mid'])
        else:
            printlog("ERROR", "Access key of the %s account is invalid. Will try to sign in with username/password." % (user))
            login(user)
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
        if third_login:
            url = "https://passport.bilibili.com/api/login/renewToken"
            params = {
                "access_key": getConfig(user, "accesskey")
            }
        else:
            url = "https://passport.bilibili.com/api/oauth2/refreshToken"
            params = {
                "access_token": getConfig(user, "accesskey"),
                "appkey": getConfig("oauth", "appkey"),
                "refresh_token": getConfig(user, "refreshtoken")
            }
        resp = bilireq(url, params=params).json()
        if resp['code'] == 0:
            if third_login:
                setConfig(user, 'expires', resp['expires'])
            else:
                setConfig(user, "accesskey", resp["data"]["access_token"])
                setConfig(user, "refreshtoken", resp["data"]["refresh_token"])
        else:
            printlog("WARNING", "Failed to renew the access key of the %s account. Will try to sign in with username/password." % (user))
            login(user)

def bilireq(url, params={}, headers={}, cookies={}, data={}, no_urlencode=False):
    from collections import OrderedDict
    headers['User-Agent'] = ''
    if data == {}: data = params
    else: data.update(params)
    if cookies == {}:
        data['appkey'] = getConfig('oauth', 'appkey')
        data['ts'] = str(int(time.time()))
        data = OrderedDict(sorted(data.items(), key=lambda data:data[0]))
        prestr = '&'.join('%s=%s' % key for key in data.items())
        data['sign'] = md5(str(prestr + getConfig('oauth', 'appsecret')).encode('utf-8')).hexdigest()
    if no_urlencode:
        data = '&'.join('%s=%s' % key for key in data.items())
    headers['Content-Type'] = 'application/x-www-form-urlencoded'
    if cookies != {}:
        data["csrf_token"] = cookies["bili_jct"]
    return requests.post(url, params=params, headers=headers, cookies=cookies, data=data, allow_redirects=False, timeout=3)
