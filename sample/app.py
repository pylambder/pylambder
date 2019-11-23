#!/usr/bin/env python3

import asyncio
import datetime
import logging
import time

from pylambder.base import Pylambder
from pylambder.websocket import WebsocketHandler

app = Pylambder()

logging.basicConfig(format='%(levelname).1s %(asctime).23s %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@app.task
def myfunc(arg1, arg2):
    print("This will be printed in the cloud")
    logger.info("This will be logged in the cloud")
    time.sleep(3)
    print("Computation finished")
    return {'sum': arg1 + arg2}


def test_callback(result):
    logger.info("Callback: {}".format(result['sum'] + 100))
    return result['sum'] + 100


if __name__ == '__main__':
    pylambder_logger = logging.getLogger('packaging')
    pylambder_logger.setLevel(logging.DEBUG)

    logger.info("Start task ----------------------------------------")
    #time.sleep(15)
    task = myfunc.delay(1, 2).set_callback(test_callback)
    myfunc.delay(5,6)
    myfunc.delay(7,8)
    myfunc.delay(9,10)   
    logger.warning("Before wait: {}".format(datetime.datetime.now().time()))
    logger.warning("Result: {}".format(task.get_result()))
    logger.warning("After wait: {}".format(datetime.datetime.now().time()))

    time.sleep(4)
    logger.warning("Now there will be exception")

    task = myfunc.delay(2, 0).set_callback(test_callback)
    logger.warning("Before wait: {}".format(datetime.datetime.now().time()))
    logger.warning("Result: {}".format(task.get_result(timeout=1000)))
    logger.warning("After wait: {}".format(datetime.datetime.now().time()))

    time.sleep(10)
    logger.warning("Exiting")
