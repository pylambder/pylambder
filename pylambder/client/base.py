"""Defines the central class of Pylambder"""

import inspect
import logging
from pathlib import Path
import os

import boto3

from pylambder import config
from pylambder.client.aws_task import CloudFunction
from pylambder.client.websocket import WebsocketHandler

logger = logging.getLogger(__name__)


class Pylambder:
    """Like Celery"""

    # tasks: Dict[aws_task.TaskId, aws_task.AWSTask]
    # websocket_handler: WebsocketHandler

    def __init__(self):
        if not self._is_lambda():
            config.ensure_loaded()
            self.api_url = self._obtain_api_url()
            self.tasks = dict()
            self.websocket_hander = WebsocketHandler(self)
            self.websocket_hander.run()

    def task(self, function):
        """Function decorator turning it into CloudFunction. Named 'task'
        because of Celery"""
        module = _getmodule(function)
        function_name = function.__name__
        return CloudFunction(function, module, function_name, self)

    @staticmethod
    def _obtain_api_url():
        cloudformation = boto3.resource('cloudformation')
        stackname = config.CLOUDFORMATION_STACK
        stack = cloudformation.Stack(stackname)
        return [x for x in stack.outputs if x['OutputKey'] == 'WebSocketURI'][0]['OutputValue']

    @staticmethod
    def _is_lambda():
        return 'LAMBDA_TASK_ROOT' in os.environ


def _getmodule(func) -> str:
    """Extract module name of a function.
    Root directory for the module name must be consistent with
    the root directory of project upload to AWS"""
    module_path = Path(inspect.getmodule(func).__file__)
    module_name = module_path.with_suffix('').name
    path = module_path.parent

    # traverse directories until project root is reached,
    # that is contains requirement.txt or pylambder_config.py
    while not ((path / 'requirements.txt').is_file() or
               (path / 'pylambder_config.py').is_file()) and \
            path not in [Path('.'), Path('/')]:
        module_name = path.name + '.' + module_name
        path = path.parent
    return module_name
