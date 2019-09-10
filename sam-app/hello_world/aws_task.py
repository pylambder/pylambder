from functools import wraps
import websockets
import inspect
import json
import asyncio

API_URL = 'wss://4e8i4x0ib3.execute-api.us-east-1.amazonaws.com/Prod'

async def apply(module, function, *args, **kwargs):
    kwargs['__incloud__'] = True
    payload = {
        'module': module,
        'function': function,
        'args': args,
        'kwargs': kwargs,
        'action': 'execute'
    }
    payload_json = json.dumps(payload)
    async with websockets.connect(API_URL) as ws:
        print("await ws.send ", payload_json)
        await ws.send(payload_json)
        print("await ws.recv")
        await ws.recv()
    return


def getmodule(func) -> str:
    modfile = inspect.getmodule(func).__file__
    name = modfile.split('/')[-1].split('.')[0]
    return name


def remote(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if kwargs.get('__incloud__', False):
            del kwargs['__incloud__']
            return f(*args, **kwargs)

        module = getmodule(f)
        function = f.__name__
        if '__incloud__' in kwargs:
            del kwargs['__incloud__']
        return apply(module, function, *args, **kwargs)
    return wrapper