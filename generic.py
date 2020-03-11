# -*- coding: utf-8 -*-

import requests
import sys
import time
from hashlib import md5
import traceback
import atexit

TELEGRAM_API = "https://api.telegram.org"

# id: From https://passport.bilibili.com/api/oauth (response_json["access_info"]["appid"])
# package: Android package name
# signature: MD5 certificate fingerprint of the officially-signed APK file (get it with `keytool -printcert -file path/to/extracted/apk/META-INF/*.RSA`)
# ak: Also known as APP_KEY
# sk: Also known as APP_SECRET
BILIBILI_ANDROID_APPS_INFO = {
    "android": {
        "id": 878,
        "package": "tv.danmaku.bili",
        "signature": "7194d531cbe7960a22007b9f6bdaa38b",
        "ak": "1d8b6e7d45233436",
        "sk": "560c52ccd288fed045859ed18bffd973"
    },
    "android_i": {
        "id": 901,
        "package": "com.bilibili.app.in",
        "signature": "7194d531cbe7960a22007b9f6bdaa38b",
        "ak": "bb3101000e232e27",
        "sk": "36efcfed79309338ced0380abd824ac1"
    },
    "android_b": {
        "id": 907,
        "package": "com.bilibili.app.blue",
        "signature": "7194d531cbe7960a22007b9f6bdaa38b",
        "ak": "07da50c9a0bf829f",
        "sk": "25bdede4e1581c836cab73a48790ca6e"
    },
    "android_tv": {
        "id": 874,
        "package": "com.xiaodianshi.tv.yst",
        "signature": "7194d531cbe7960a22007b9f6bdaa38b",
        "ak": "4409e2ce8ffd12b8",
        "sk": "59b43e04ad6965f34319062b478f83dd"
    },
    "biliLink": {
        "id": 865,
        "package": "com.bilibili.bilibililive",
        "signature": "de7b332d94008008bbe7e0b80d87d859",
        "ak": "37207f2beaebf8d7",
        "sk": "e988e794d4d4b6dd43bc0e89d6e90c43"
    },
    "android_comic": {
        "id": 982,
        "package": "com.bilibili.comic",
        "signature": "b341c01700752a4915d075409b6fec99",
        "ak": "cc8617fd6961e070",
        "sk": "3131924b941aac971e45189f265262be"
    },
    "android_bbq": {
        "id": 986,
        "package": "com.bilibili.qing",
        "signature": "ab055c40257e280aa8ea17a0da77efe9",
        "ak": "cc578d267072c94d",
        "sk": "ffb6bb4c4edae2566584dbcacfc6a6ad"
    }
}

def printlog(log_type, message):
    log_message = "[%s] %s" % (log_type, message)
    print(log_message, flush=True)
    cwd = sys.path[0]
    if cwd != "":
        with open(cwd + "/cathy.log", "a", encoding="utf-8") as logfile:
            logfile.write(log_message + "\n")
    if getConfig("telegram", "token") != "" and getConfig("telegram", "log_channel") != "":
        url = TELEGRAM_API + "/bot" + getConfig("telegram", "token") + "/sendMessage"
        try: requests.get(url, params = {"chat_id": int(getConfig("telegram", "log_channel")), "text": log_message, "disable_notification": log_type != "ERROR"}, timeout=5)
        except: pass

def convertTime(dt):
    if dt.tzinfo is None:
        return int(time.mktime(dt.timetuple()))
    else:
        from datetime import datetime
        import pytz
        return int((dt - datetime(1970, 1, 1, tzinfo=pytz.utc)).total_seconds())

def getConfig(section, entry=None):
    from configparser import ConfigParser, NoSectionError
    config = ConfigParser()
    cwd = sys.path[0]
    if cwd == "": cwd = "."
    config.read(cwd + "/config.ini", encoding="utf-8")
    try:
        if entry:
            return config.get(section, entry)
        return dict(config.items(section))
    except NoSectionError:
        time.sleep(5)
        return getConfig(section, entry)

def setConfig(section, entry, value):
    from configparser import ConfigParser
    value = str(value).replace("%", "%%")
    config = ConfigParser()
    cwd = sys.path[0]
    if cwd == "": cwd = "."
    config.read(cwd + "/config.ini")
    config.set(section, entry, str(value))
    with open(cwd + "/config.ini", "w", encoding="utf-8") as configFile:
        config.write(configFile)

def getBiliCookie(user, force_client="biliLink"):
    from collections import OrderedDict
    url = "https://passport.bilibili.com/api/login/sso"
    params = {
        "appkey": BILIBILI_ANDROID_APPS_INFO[force_client]["ak"],
        "access_key": getConfig(user, "accesskey"),
        "ts": str(int(time.time()))
    }
    params = OrderedDict(sorted(params.items(), key=lambda params:params[0]))
    prestr = "&".join("%s=%s" % key for key in params.items())
    params["sign"] = md5(str(prestr + BILIBILI_ANDROID_APPS_INFO[force_client]["sk"]).encode("utf-8")).hexdigest()
    resp = requests.get(url, params=params, allow_redirects=False, timeout=3)
    return resp.cookies

def login(user=None, username="", password=""):
    import rsa
    from base64 import b64encode
    from urllib.parse import quote_plus as urlencode
    flag = False
    if user:
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
    encryptor = rsa.PublicKey.load_pkcs1_openssl_pem(key["key"].encode("utf-8"))
    password = b64encode(rsa.encrypt((key["hash"] + password).encode("utf-8"), encryptor)).decode("utf-8")
    username = urlencode(username)
    password = urlencode(password)
    resp = bilireq("https://passport.bilibili.com/api/v2/oauth2/login", data={"username": username, "password": password}, no_urlencode=True).json()
    if resp["code"] == -105:
        printlog("ERROR", "bilibili is requiring a CAPTCHA challenge. Please try again later.")
        return
    elif resp["code"] != 0:
        printlog("ERROR", "Failed to sign in to account %s with username/password: %s" % (user, resp["message"]))
        return
    if user:
        setConfig(user, "expires", resp["ts"] + resp["data"]["token_info"]["expires_in"])
        setConfig(user, "uid", resp["data"]["token_info"]["mid"])
        setConfig(user, "accesskey", resp["data"]["token_info"]["access_token"])
        setConfig(user, "refreshtoken", resp["data"]["token_info"]["refresh_token"])
    else:
        printlog("DEBUG", resp)

def checkToken(user, firstrun=False, force_client="biliLink"):
    #if firstrun:
        #callback_url = "https://link.acg.tv/forum.php"
        #auth_url = "https://passport.bilibili.com/register/third.html?api=%s&appkey=%s&sign=%s" % (callback_url, BILIBILI_ANDROID_APPS_INFO["android"]["ak"], md5(str("api=%s%s" % (callback_url, BILIBILI_ANDROID_APPS_INFO["android"]["sk"])).encode('utf-8')).hexdigest())
        #check_auth_url = auth_url.replace('https://passport.bilibili.com/register/third.html', 'https://passport.bilibili.com/login/app/third')
    if getConfig(user, "accesskey") == "":
        printlog("ERROR", "Access key of the %s account is missing. Will try to sign in with username/password." % (user))
        login(user)

    if firstrun or getConfig(user, "expires") == "" or getConfig(user, "uid") == "":
        url = "https://passport.bilibili.com/api/oauth"
        params = {
            "access_key": getConfig(user, "accesskey")
        }
        resp = requests.get(url, params=params).json()
        if resp["code"] == 0:
            setConfig(user, "expires", resp["access_info"]["expires"])
            setConfig(user, "uid", resp["access_info"]["mid"])
            if resp["access_info"]["appid"] not in [client["id"] for client in BILIBILI_ANDROID_APPS_INFO.values()]:
                printlog("ERROR", "Access key of the %s account is not supported." % (user))
                printlog("INFO", "Attempting to sign in with username/password.")
                login(user)
            else:
                access_key_appid = resp["access_info"]["appid"]
        else:
            printlog("ERROR", "Access key of the %s account is invalid." % (user))
            printlog("INFO", "Attempting to sign in with username/password.")
            #printlog("ERROR", "You can also generate one at %s" % (auth_url))
            login(user)

    if getConfig(user, "refreshtoken") == "":
        printlog("INFO", "Refresh token of the %s account is missing. Will try to generate one." % (user))
        for client in BILIBILI_ANDROID_APPS_INFO.keys():
            if access_key_appid != BILIBILI_ANDROID_APPS_INFO[client]["id"]: continue
            url = "https://passport.bilibili.com/api/oauth2/authorizeByApp"
            data = {
                "access_token": getConfig(user, "accesskey"),
                "package": BILIBILI_ANDROID_APPS_INFO[force_client]["package"],
                "signature": BILIBILI_ANDROID_APPS_INFO[force_client]["signature"],
                "target_appkey": BILIBILI_ANDROID_APPS_INFO[force_client]["ak"]
            }
            resp = bilireq(url, data=data, force_client=client).json()
            if resp["code"] == 0: break
        #if resp["code"] == -900:
        #    printlog("ERROR", "Cannot determine the corresponding client for the access key of the %s account." % (user))
        if resp["code"] != 0:
            printlog("ERROR", "Failed to generate refresh token for the %s account." % (user))
            printlog("INFO", "Attempting to sign in with username/password.")
            login(user)
        url = "https://passport.bilibili.com/api/v2/oauth2/access_token"
        params = {
            "appkey": BILIBILI_ANDROID_APPS_INFO[force_client]["ak"],
            "code": resp["data"]["code"],
            "grant_type": "authorization_code"
        }
        resp = bilireq(url, params=params, force_get=True).json()
        if resp["code"] != 0:
            printlog("ERROR", "Failed to generate refresh token for the %s account." % (user))
            printlog("INFO", "Attempting to sign in with username/password.")
            login(user)
        else:
            setConfig(user, "expires", resp["ts"] + resp["data"]["token_info"]["expires_in"])
            setConfig(user, "uid", resp["data"]["token_info"]["mid"])
            setConfig(user, "accesskey", resp["data"]["token_info"]["access_token"])
            setConfig(user, "refreshtoken", resp["data"]["token_info"]["refresh_token"])

    if getConfig("host", "roomid") == "":
        url = "https://space.bilibili.com/ajax/live/getLive"
        params = {
            "mid": getConfig("host", "uid")
        }
        response = requests.get(url, params=params, timeout=3).json()
        if response["status"]:
            setConfig("host", "roomid", response["data"])
        else:
            printlog("ERROR", "Failed to get room ID of host.")

    if int(getConfig(user, "expires")) - int(time.time()) < 15*24*60*60:
        printlog("INFO", "Refreshing access key of the %s account." % (user))
        url = "https://passport.bilibili.com/api/v2/oauth2/refresh_token"
        data = {
            "access_key": getConfig(user, "accesskey"),
            "appkey": BILIBILI_ANDROID_APPS_INFO[force_client]["ak"],
            "refresh_token": getConfig(user, "refreshtoken")
        }
        resp = bilireq(url, data=data).json
        if resp["code"] == 0:
            setConfig(user, "expires", resp["ts"] + resp["data"]["token_info"]["expires_in"])
            setConfig(user, "uid", resp["data"]["token_info"]["mid"])
            setConfig(user, "accesskey", resp["data"]["token_info"]["access_token"])
            setConfig(user, "refreshtoken", resp["data"]["token_info"]["refresh_token"])
        else:
            printlog("WARNING", "Failed to renew the access key of the %s account. API says %s" % (user, resp["message"]))
            printlog("WARNING", "Will try to sign in with username/password.")
            login(user)

def bilireq(url, params={}, headers={}, cookies=None, data={}, no_urlencode=False, force_get=False, host_ip=None, force_client="biliLink"):
    s = requests.Session()
    if host_ip:
        import host_header_ssl_sni
        s.mount("https://", host_header_ssl_sni.HostHeaderSSLAdapter())
        host = url.replace("https://", "").split("/")[0]
        headers["Host"] = host
        url = url.replace(host, host_ip)
    from collections import OrderedDict
    headers["User-Agent"] = ""
    if data == {}: data = params
    else: data.update(params)
    if cookies == None:
        data["appkey"] = BILIBILI_ANDROID_APPS_INFO[force_client]["ak"]
        data["ts"] = str(int(time.time()))
        data = OrderedDict(sorted(data.items(), key=lambda data:data[0]))
        prestr = "&".join("%s=%s" % key for key in data.items())
        data["sign"] = md5(str(prestr + BILIBILI_ANDROID_APPS_INFO[force_client]["sk"]).encode("utf-8")).hexdigest()
    if no_urlencode:
        data = "&".join("%s=%s" % key for key in data.items())
    if cookies != None:
        data["csrf_token"] = cookies["bili_jct"]
        data["csrf"] = cookies["bili_jct"]
    if force_get:
        return s.get(url, params=data, headers=headers, cookies=cookies, allow_redirects=False, timeout=10)
    else:
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        return s.post(url, params=params, headers=headers, cookies=cookies, data=data, allow_redirects=False, timeout=10)
