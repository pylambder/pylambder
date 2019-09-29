from functools import wraps
import websockets
import inspect
import json
import asyncio
import boto3


class AWSTask:
    def __init__(self, f, module, function):
        self.module = module
        self.function = function
        self.f = f

    def run(self, *args, **kwargs):
        return self.f(*args, **kwargs)

    def delay(self, ws_handler, *args, **kwargs):
        payload = self.get_exeucte_payload(args, kwargs)
        ws_handler.schedule(payload)

    def get_exeucte_payload(self, args, kwargs) -> str:
        payload_execute = {
            'module': self.module,
            'function': self.function,
            'args': args,
            'kwargs': kwargs,
            'action': 'execute'
        }
        return json.dumps(payload_execute)


def remote(f):
    module = getmodule(f)
    function = f.__name__
    return AWSTask(f, module, function)


async def apply(module, function, *args, **kwargs):
    kwargs['__incloud__'] = True
    execute_payload = get_exeucte_payload(module, function, args, kwargs)
    cloudformation = boto3.resource('cloudformation')
    stack = cloudformation.Stack('websocket-task-poc')
    API_URL = [x for x in stack.outputs if x['OutputKey'] == 'WebSocketURI'][0]['OutputValue']
    async with websockets.connect(API_URL) as ws:
        print("await ws.send ", execute_payload)
        await ws.send(execute_payload)
        print("await ws.recv")
        response = await ws.recv()
        response_term = json.loads(response)
        request_id = response_term['requestId']
        print("Result: ", response_term)
        result_payload = get_result_payload(request_id)
        print("await ws.send ", result_payload)
        await ws.send(result_payload)
        result_response = await ws.recv()
        return result_response

def get_exeucte_payload(module, function, args, kwargs) -> str:
    payload_execute = {
        'module': module,
        'function': function,
        'args': args,
        'kwargs': kwargs,
        'action': 'execute'
    }
    return json.dumps(payload_execute)

def get_result_payload(request_id) -> str:
    payload_result = {
        'RequestId': request_id,
        'action': 'result'
    }
    return json.dumps(payload_result)
    
def getmodule(func) -> str:
    modfile = inspect.getmodule(func).__file__
    name = modfile.split('/')[-1].split('.')[0]
    return name
