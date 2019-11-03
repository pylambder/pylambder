""" This module contains the websocket connection with AWS logic."""
import asyncio
import json
import logging
import threading

import boto3
import janus
import websockets

from pylambder import aws_task, config

QUEUE_MAX_SIZE = 1000

LOGGER = logging.getLogger(__name__)


class WebsocketHandler:
    """ This class handles websocket connection to AWS, manages sending
    request and response handling. When ran it will work in separate thread.
    Instantination of this class does not yet run the websocket
    connection."""

    def __init__(self, app=None):
        self.queue = None
        self.worker = None
        self.started = False
        self.app = app

    def run(self):
        """Starts the websocket connection in separate thread with new
        asyncio event loop"""
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
        """Receiver task that awaits for messages on the websocket."""
        async for msg in websocket:
            LOGGER.debug(F"Received message: {msg}")
            self.handle_message(msg)

    def handle_message(self, msg):
        """Received message handling logic. This function will be invoked on
        all received messages."""
        decoded = json.loads(msg)
        task_uuid = decoded['uuid']
        if 'status' in decoded:
            task_status = aws_task.TaskStatus(int(decoded['status']))
            LOGGER.info(F"Task {task_uuid} changed status to {task_status.name}")
            self.app.tasks[task_uuid].status = task_status
            if task_status in (aws_task.TaskStatus.FINISHED, aws_task.TaskStatus.FAILED):
                task_result = decoded['result']
                LOGGER.info(
                    F"Task {task_uuid} changed status to {task_status.name} with result {task_result}")
                self.app.tasks[task_uuid].handle_status_with_result(task_status, task_result)
                del self.app.tasks[task_uuid]
        else:
            LOGGER.warning(F"Unexpected message: {msg}")

    async def _sender(self, websocket):
        """Read messages from the queue and sent them through the websocket"""
        while True:
            LOGGER.debug("Waiting for a message to appear in queue")
            task = await self.queue.async_q.get()
            LOGGER.debug("Sending task {}".format(task))
            await websocket.send(task)

    def _websocket_thread(self):
        """Websocket loop start function. It is executed in new thread."""
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._websocket_loop())

    async def _websocket_loop(self):
        """Main loop of the websocket."""
        api_url = self.app.api_url
        LOGGER.info(F"Opening websocket connection to {api_url}")
        async with websockets.connect(api_url) as websocket:
            LOGGER.info("Websocket connected")
            consumer_task = asyncio.create_task(self._sender(websocket))
            producer_task = asyncio.create_task(self._receiver(websocket))
            while True:
                await asyncio.wait([producer_task, consumer_task],
                                   return_when=asyncio.FIRST_COMPLETED)

    def schedule(self, task):
        """Schedules new task to be sent in the queue."""
        payload = {
            'action': 'execute',
            'module': task.function.module,
            'function': task.function.function,
            'args': task.args,
            'kwargs': task.kwargs,
            'uuid': task.id
        }
        self.queue.sync_q.put(json.dumps(payload))
