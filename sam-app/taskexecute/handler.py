import json
import os
import logging

import importlib
import time

import boto3
import botocore

from enum import Enum

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def lambda_handler(event, context):
    logger.debug("Task execute event: {}".format(event))
    logger.debug("Task execute context: {}".format(context))

    body, request_id, domain_name, stage, connection_id, request_id = unpack_event(event)
    request_id = context.aws_request_id
    apigw_management = create_socket_client(domain_name, stage)
    uuid = body['uuid']
    function, args, kwargs = get_function_with_args(body)

    scheduledResponse = {
        'requestId': request_id,
        'uuid': uuid,
        'status': "scheduled"
    }
    status = send_to_client(connection_id, scheduledResponse, apigw_management)
    if(status['statusCode'] != 200):
        return status 
    
    result = function.run(*args, **kwargs)

    status = send_to_client(connection_id, {"uuid": uuid, "result": result}, apigw_management)
    if(status['statusCode'] != 200):
        return status
    
    store_result(result, uuid)

    return {'statusCode': 200,
             'body': 'ok'}
    
def send_to_client(connection_id, data, apigw_management):
    try:
        logger.debug("Send result to websocket")
        _ = apigw_management.post_to_connection(ConnectionId=connection_id,
                                                     Data=json.dumps(data))
        logger.debug("Sent result to websocket")
        return  {'statusCode': 200, 'body': 'ok'}
    except botocore.exceptions.ClientError as e:
        logger.debug('post_to_connection failed: %s' % e)
        return {'statusCode': 500, 'body': 'something went wrong'}
    
def create_socket_client(domain_name, stage):
    logger.debug("Creating sockets client")
    return boto3.client('apigatewaymanagementapi', endpoint_url=F"https://{domain_name}/{stage}")

def unpack_event(event):
    request_context = event.get('requestContext', {})
    
    body = json.loads(event.get('body', '{}'))
    request_id = request_context.get('requestId')
    domain_name = request_context.get('domainName')
    stage = request_context.get('stage')
    connection_id = request_context.get('connectionId')
    
    if (body and stage and request_id and connection_id and domain_name) is None:
        logger.warning("Bad request: {} and {} and {} and {} and {}".format(body, stage, request_id, connection_id, domain_name))
        return { 'statusCode': 400,
                 'body': 'bad request'}
        
    return (body, request_id, domain_name, stage, connection_id, request_id)

def get_function_with_args(body):
    module_name = body['module']
    function_name = body['function']
    args, kwargs = body['args'], body['kwargs']

    logger.debug("Importing module '{}'".format(module_name))
    module = importlib.import_module(module_name, package=None)
    return getattr(module, function_name), args, kwargs

def store_result(result, request_id):
    result_json = json.dumps(result)
    
    resultData = {
        'RequestId': {'S': request_id},
        'Result': {'S': result_json}
    }

    dynamodb = boto3.client('dynamodb')
    logger.debug("Storing call result")
    dynamodb.put_item(TableName=os.environ['TABLE_NAME'], Item=resultData)
