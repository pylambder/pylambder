"""Defines the central class of Pylambder"""

from typing import Dict
from pylambder import aws_task
import inspect
import pylambder.websocket
from pylambder.websocket import WebsocketHandler
from pylambder.aws_task import CloudFunction


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
        self.tasks = dict()
        self.websocket_hander = WebsocketHandler(self)

    def task(self, f):
        """Function decorator turning it into CloudFunction. Named 'task'
        becuase of Celery"""
        module = getmodule(f)
        function = f.__name__
        return CloudFunction(f, module, function, self)
