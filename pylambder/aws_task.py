import asyncio
import inspect
import json
import logging
import uuid
from enum import IntEnum
from functools import wraps
from threading import Event, Thread

import boto3
import websockets

from pylambder import config

TaskId = str

logger = logging.getLogger(__name__)

class CloudFunction:
    def __init__(self, f, module, function, pylambder_app):
        self.module = module
        self.function = function
        self.f = f
        self.app = pylambder_app

    def run(self, *args, **kwargs):
        return self.f(*args, **kwargs)

    def delay(self, *args, **kwargs):
        awstask = AWSTask(self, args, kwargs)
        self.app.tasks[awstask.id] = awstask
        self.app.websocket_hander.schedule(awstask)
        return awstask


class TaskStatus(IntEnum):
    REQUESTED = 1  # the default state after requesting task execution
    SENT = 2  # message scheduling the task sent to cloud
    STARTED = 3  # the cloud confirmed receiving the task
    FINISHED = 4  # task results received
    FAILED = 5  # the executed function threw an exception
    META_FAILED = 6  # pylambder failed to execute the task


class AWSTask:
    """Instance of a CloudFunction invocation"""

    def __init__(self, cloud_function: CloudFunction, call_args, call_kwargs):
        self.function = cloud_function
        self.id = str(uuid.uuid4())
        self.status = TaskStatus.REQUESTED
        self.args = call_args
        self.kwargs = call_kwargs
        self.result = None
        self.done_flag = Event()
        self.callback = None
        self.callback_done = Event()
        self.callback_thread = None

    def set_callback(self, callback):
        if self.status == TaskStatus.FINISHED:
            self.result = callback(self.result)
        else:
            self.callback = callback
        return self

    def __invoke_callback(self, status, result):
        self.result = self.callback(result)
        self.status = status
        self.callback_done.set()

    def handle_status_with_result(self, status, result):
        if status == TaskStatus.FINISHED:
            if self.callback is None:
                self.status = status
                self.result = result
                self.done_flag.set()
            else:
                self.status = status
                self.result = result
                self.done_flag.set()

                self.callback_thread = Thread(target=self.__invoke_callback, args=(status, result,))
                self.callback_thread.setDaemon(True)
                self.callback_thread.run()
        elif status == TaskStatus.FAILED:
            self.status = status
            # create exception object which repr() we have
            self.result = eval(result)
            self.done_flag.set()

    def get_result(self, timeout: float = None):
        if self.done_flag.wait(timeout):
            if self.status == TaskStatus.FINISHED:
                return self.result
            elif self.status == TaskStatus.FAILED:
                # FIXME better way of rethrowing the exception
                raise self.result
        else:
            # TODO use pylambder exception - this one is related to system calls
            raise TimeoutError()

    def wait(self, timeout=None):
        if self.status in (TaskStatus.FAILED, TaskStatus.META_FAILED):
            return None
        if self.callback is None:
            self.done_flag.wait(timeout)
        else:
            self.callback_done.wait(timeout)


def get_result_payload(request_id) -> str:
    payload_result = {
        'RequestId': request_id,
        'action': 'result'
    }
    return json.dumps(payload_result)
