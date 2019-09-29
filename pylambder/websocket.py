import websockets
import json
import asyncio
import boto3
import threading
import janus

QUEUE_MAX_SIZE = 1000

class WebsocketHandler:
    def __init__(self):
        self.queue = None
        self.worker = None
        self.started = False
     
    def run(self):
        if self.started: 
            raise Exception("Handler already running")
        else: 
            self.loop = asyncio.new_event_loop()
            self.queue = janus.Queue(loop=self.loop)
            self.worker = threading.Thread(target=self._websocket_thread)
            self.worker.setDaemon(True)
            self.worker.start()
            self.started = True

    async def _websocket_producer(self, websocket):
        async for msg in websocket:
            print(msg)

    async def _websocket_consumer(self, websocket):
        while True:
            task = await self.queue.async_q.get()
            print("Task: {}", task)
            await websocket.send(task)
            result = await websocket.rcv()
            print(result)

    def _websocket_thread(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._websocket_loop())

    async def _websocket_loop(self):
        cloudformation = boto3.resource('cloudformation')
        stack = cloudformation.Stack('websocket-task-poc')
        API_URL = [x for x in stack.outputs if x['OutputKey'] == 'WebSocketURI'][0]['OutputValue']
        print("Api URL: {}", API_URL)
        async with websockets.connect(API_URL) as ws:
            consumer_task = asyncio.ensure_future(self._websocket_consumer(ws))
            producer_task = asyncio.ensure_future(self._websocket_producer(ws))
            while True:
                await asyncio.wait([consumer_task, producer_task], return_when=asyncio.FIRST_COMPLETED)

    def schedule(self, aws_task):
        self.queue.sync_q.put(aws_task)