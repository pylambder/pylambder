#!/usr/bin/env python3

import asyncio
import datetime
import logging
import time

from pylambder.base import Pylambder
from pylambder.websocket import WebsocketHandler

app = Pylambder()

logging.basicConfig(format='%(asctime)s %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@app.task
def myfunc(arg1, arg2):
    print("This will be logged in the cloud")
    time.sleep(1)
    print("Computation finished")
    return {'sum': arg1 + arg2}


if __name__ == '__main__':
    pylambder_logger = logging.getLogger('pylambder')
    pylambder_logger.setLevel(logging.DEBUG)

    logger.info("Start task")
    myfunc.delay(1, 2)
    time.sleep(10)
    print("Task scheduled")
