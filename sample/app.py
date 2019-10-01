#!/usr/bin/env python3

import time
import datetime
import asyncio
from pylambder.websocket import WebsocketHandler
from pylambder.base import Pylambder

app = Pylambder()

@app.task
def myfunc(arg1, arg2):
    print("This will be logged in the cloud")
    time.sleep(1)
    print("Computation finished")
    return {'sum': arg1 + arg2}

if __name__ == '__main__':
    print("{} Start task".format(datetime.datetime.now().time()))
    ws_handler = WebsocketHandler()
    ws_handler.run()
    myfunc.delay(ws_handler, 1, 2)
    time.sleep(10)
    print("{} Task scheduled".format(datetime.datetime.now().time()))
