"""Defines the central class of Pylambder"""

from typing import Dict
from pylambder import aws_task, websocket



class Pylambder:
    """Like Celery"""

    tasks: Dict[aws_task.TaskId, aws_task.AWSTask]
    websocket_hander: websocket.WebsocketHandler

    def __init__(self):
        self.tasks = dict()
        self.websocket_hander = websocket.WebsocketHandler(self)
