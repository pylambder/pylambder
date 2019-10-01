"""Defines the central class of Pylambder"""

from typing import Dict
from pylambder import aws_task
import pylambder.websocket
from pylambder.websocket import WebsocketHandler


class Pylambder:
    """Like Celery"""

    # tasks: Dict[aws_task.TaskId, aws_task.AWSTask]
    # websocket_hander: WebsocketHandler

    def __init__(self):
        self.tasks = dict()
        self.websocket_hander = WebsocketHandler(self)
