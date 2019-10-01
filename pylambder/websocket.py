import asyncio
import json
import logging
import threading

import boto3
import janus
import websockets

from pylambder import config
from pylambder import aws_task

QUEUE_MAX_SIZE = 1000

logger = logging.getLogger(__name__)


class WebsocketHandler:
    def __init__(self, app=None):
        self.queue = None
        self.worker = None
        self.started = False
        self.app = app

    def run(self):
        if self.started:
            raise Exception("Handler already running")
        else:
            self.loop = asyncio.new_event_loop()
            self.loop.set_debug(True)
            self.queue = janus.Queue(loop=self.loop)
            self.worker = threading.Thread(target=self._websocket_thread)
            self.worker.setDaemon(True)
            self.worker.start()
            self.started = True

    async def _receiver(self, websocket):
        async for msg in websocket:
            logger.debug("Received message: {}".format(msg))
            self.handle_message(msg)

    def handle_message(self, msg):
        decoded = json.loads(msg)
        task_uuid = decoded['uuid']
        if 'status' in decoded:
            task_status = aws_task.TaskStatus(int(decoded['status']))
            logger.info(F"Task {task_uuid} changed status to {task_status}")
            self.app.tasks[task_uuid].status = task_status
            if task_status in (aws_task.TaskStatus.FINISHED, aws_task.TaskStatus.FAILED):
                task_result = decoded['result']
                logger.info(F"Task {task_uuid} changed status to {task_status} with result {task_result}")
                self.app.tasks[task_uuid].handle_status_with_result(task_status, task_result)
                del self.app.tasks[task_uuid]
        else:
            logger.warn(F"Unexpected message: {msg}")

    async def _sender(self, websocket):
        """Read messages from the queue and sent them through the websocket"""
        while True:
            logger.debug("Waiting for a message to appear in queue")
            task = await self.queue.async_q.get()
            logger.debug("Sending task {}".format(task))
            await websocket.send(task)

    def _websocket_thread(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._websocket_loop())

    async def _websocket_loop(self):
        api_url = self.app.api_url
        logger.info("Opening websocket connection to {}".format(api_url))
        async with websockets.connect(api_url) as ws:
            logger.info("Websocket connected")
            consumer_task = asyncio.create_task(self._sender(ws))
            producer_task = asyncio.create_task(self._receiver(ws))
            while True:
                done, pending = await asyncio.wait([producer_task, consumer_task], return_when=asyncio.FIRST_COMPLETED)
                # rethrow exceptions
                # (x.result() for x in done + pending)

    def schedule(self, aws_task):
        payload = {
            'action': 'execute',
            'module': aws_task.function.module,
            'function': aws_task.function.function,
            'args': aws_task.args,
            'kwargs': aws_task.kwargs,
            'uuid': aws_task.id
        }
        self.queue.sync_q.put(json.dumps(payload))
