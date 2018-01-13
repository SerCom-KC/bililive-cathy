# Code adapted from https://github.com/GoKey/bilibili-danmu
# -*- coding: utf-8 -*-
import websocket # also pip install websocket-client please
import threading
import time
import json
import struct
from generic import *
import logging

def on_message(ws, data):
    if (not data) or len(data) == 0:
        ws.close()
        return
    if len(data) == 16:
        printlog("INFO", "Successfully connected with danmaku websocket server.")
        return
    if len(data) == 20:
        return
    try:
        response = json.loads(data[16:])
    except Exception:
        printlog("ERROR", "Failed to parse websocket message.")
        return
    if(response['cmd'] == 'DANMU_MSG'):
        from main import danmakuIdentify
        danmakuIdentify(response['info'][2][0], response['info'][2][1], response['info'][1])
    if(response['cmd'] == 'PREPARING'):
        printlog("INFO", "Looks like the live switch is OFF. The time now is " + time.ctime())
        from main import startLive, restartStream
        startLive()
        restartStream()
    return

def on_error(ws, error):
    printlog("ERROR", "A websocket error occurred.")
    print(error)

def on_close(ws):
    printlog("WARNING", "Disconnected with danmaku websocket server.")

def listenDanmaku():
    global bili_roomid
    bili_roomid = getRoomID()
    logging.basicConfig()
    ws = websocket.WebSocketApp("ws://broadcastlv.chat.bilibili.com:2244/sub", on_message=on_message, on_error=on_error, on_close=on_close)
    ws.on_open = on_open
    ws.run_forever()

def on_open(ws):
    def run(*args):
        global bili_roomid
        data = '\x00\x00\x00\x5a\x00\x10\x00\x01\x00\x00\x00\x07\x00\x00\x00\x01{"uid":0,"roomid":'+ str(bili_roomid) +',"protover":1,"platform":"web","clientver":"1.2.5"}'
        ws.send(data, opcode=websocket.ABNF.OPCODE_BINARY)

    def heart():
        while True:
            try:
                ws.send("\x00\x00\x00\x1f\x00\x10\x00\x01\x00\x00\x00\x02\x00\x00\x00\x01[object Object]", opcode=websocket.ABNF.OPCODE_BINARY)
            except:
                break
            time.sleep(30)

    __threads__ = []
    run()
    __threads__.append(threading.Thread(target=heart))
    for t in __threads__:
        t.setDaemon(True)
        t.start()