"""Defines the central class of Pylambder"""

import inspect
import os

import boto3

from pylambder import config
from pylambder.aws_task import CloudFunction
from pylambder.websocket import WebsocketHandler


def getmodule(func) -> str:
    """Extract module name of a function"""
    modfile = inspect.getmodule(func).__file__
    name = modfile.split('/')[-1].split('.')[0]
    return name


class Pylambder:
    """Like Celery"""

    # tasks: Dict[aws_task.TaskId, aws_task.AWSTask]
    # websocket_hander: WebsocketHandler

    def __init__(self):
        if not self._is_lambda():
            self.api_url = self._obtain_api_url()
            self.tasks = dict()
            self.websocket_hander = WebsocketHandler(self)
            self.websocket_hander.run()

    def task(self, function):
        """Function decorator turning it into CloudFunction. Named 'task'
        becuase of Celery"""
        module = getmodule(function)
        function = function.__name__
        return CloudFunction(function, module, function, self)

    @staticmethod
    def _obtain_api_url():
        cloudformation = boto3.resource('cloudformation')
        stackname = config.get('cloudformation_stack')
        stack = cloudformation.Stack(stackname)
        return [x for x in stack.outputs if x['OutputKey'] == 'WebSocketURI'][0]['OutputValue']

    @staticmethod
    def _is_lambda():
        return 'LAMBDA_TASK_ROOT' in os.environ
