# Code adapted from https://github.com/GoKey/bilibili-danmu
# -*- coding: utf-8 -*-
import websocket # also pip install websocket-client please
import threading
import time
import json
import struct
from generic import *
import logging

def danmakuParse(message):
    response = json.loads(message)
    if response['cmd'] == 'DANMU_MSG':
        if str(response['info'][2][0]) == getConfig('assist', 'uid'):
            printlog("INFO", "Danmaku sent: " + response['info'][1])
            return
        printlog("INFO", "New danmaku from " + response['info'][2][1] + " (" + str(response['info'][2][0]) + ") at " + str(response['info'][0][4]) + ": " + response['info'][1])
        from plugin import commandParse
        commandParse({"from": "bili-danmaku", "uid": response['info'][2][0], "username": response['info'][2][1]}, response['info'][1])
    if response['cmd'] == 'PREPARING': # or response['cmd'] == 'ROOM_SILENT_OFF'
        printlog("INFO", "Looks like the live switch is OFF.")
        from main import startLive, restartStream
        startLive()
        restartStream()
    return

def on_message(ws, data):
    if (not data) or len(data) == 0:
        ws.close()
        return
    if len(data) == 16:
        printlog("INFO", "Successfully connected with danmaku websocket server.")
        from main import isLiving, startLive, restartStream
        if not isLiving():
            printlog("INFO", "Looks like the live switch is OFF.")
            startLive()
            restartStream()
        return
    if len(data) == 20:
        return
    count = 0
    for i in range(0, len(data), 1):
        if data[i] == 123:
            if count == 0:
                start = i
            count = count + 1
        elif data[i] == 125:
            if count == 1:
                danmakuParse(data[start:i+1].decode())
            count = count - 1
    return

def on_error(ws, error):
    printlog("ERROR", "A websocket error occurred: " + str(error))

def on_close(ws):
    printlog("WARNING", "Disconnected with danmaku websocket server.")

def listenDanmaku():
    logging.basicConfig()
    ws = websocket.WebSocketApp("ws://broadcastlv.chat.bilibili.com:2244/sub", on_message=on_message, on_error=on_error, on_close=on_close)
    ws.on_open = on_open
    while True:
        try:
            ws.run_forever()
        except Exception:
            printlog("ERROR", "Unexpected error occurred on websocket.")
            printlog("TRACEBACK", "\n" + traceback.format_exc())

def on_open(ws):
    def run(*args):
        data = '\x00\x00\x00\x5a\x00\x10\x00\x01\x00\x00\x00\x07\x00\x00\x00\x01{"uid":0,"roomid":'+ getConfig('host', 'roomid') +',"protover":1,"platform":"web","clientver":"1.2.5"}'
        ws.send(data, opcode=websocket.ABNF.OPCODE_BINARY)

    def heart():
        while True:
            try:
                ws.send("\x00\x00\x00\x1f\x00\x10\x00\x01\x00\x00\x00\x02\x00\x00\x00\x01[object Object]", opcode=websocket.ABNF.OPCODE_BINARY)
            except Exception:
                break
            time.sleep(30)

    __threads__ = []
    run()
    __threads__.append(threading.Thread(target=heart))
    for t in __threads__:
        t.setDaemon(True)
        t.start()
