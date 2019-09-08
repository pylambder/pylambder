#!/usr/bin/env python3

import time
import datetime
from aws_task import remote

@remote
def myfunc(arg1, arg2):
    print("This will be logged in the cloud")
    time.sleep(5)
    print("Computation finished")
    return {'sum': arg1 + arg2}

if __name__ == '__main__':
    print("{} Start task".format(datetime.datetime.now().time()))
    result = myfunc(3, 4)
    print("{} Task result: {}".format(datetime.datetime.now().time(), result))
