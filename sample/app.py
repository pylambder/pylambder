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
    time.sleep(5)
    #raise NameError("My name is not myfunc, for you it's mr. myfunc!")
    print("Computation finished")
    return {'sum': arg1 + arg2}


def test_callback(result):
    print("Callback: {}".format(result['sum'] + 100))
    return result['sum'] + 100


if __name__ == '__main__':
    pylambder_logger = logging.getLogger('pylambder')
    pylambder_logger.setLevel(logging.DEBUG)

    logger.info("Start task")
    task = myfunc.delay(1, 2).set_callback(test_callback)
    logger.warning("Before wait: {}".format(datetime.datetime.now().time()))
    logger.warning("After wait: {}".format(datetime.datetime.now().time()))
    #logger.warning("Result: {}".format(task.get_result()))
    time.sleep(10)
    logger.warning("Exiting")
