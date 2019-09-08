from functools import wraps
import websocket
import inspect
import json
import asyncio

API_URL = ''

async def apply(module, function, *args, **kwargs):
    kwargs['__incloud__'] = True
    payload = {
        'module': module,
        'function': function,
        'args': args,
        'kwargs': kwargs
    }
    async with websocket.connect(API_URL) as websocket:
        await websocket.send(payload)
        await websocket.rcv()
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