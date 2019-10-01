from functools import wraps
import websockets
import inspect
import json
import asyncio
import boto3
import uuid
from enum import Enum
from pylambder import config

TaskId = str


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



class TaskStatus(Enum):
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


def get_result_payload(request_id) -> str:
    payload_result = {
        'RequestId': request_id,
        'action': 'result'
    }
    return json.dumps(payload_result)
