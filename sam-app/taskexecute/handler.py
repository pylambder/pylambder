import json
import os
import logging

import importlib
import time

import boto3
import botocore

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

dynamodb = boto3.client('dynamodb')


def lambda_handler(event, context):
    logger.debug("Task execute event: {}".format(event))
    logger.debug("Task execute context: {}".format(context))

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

    request_id = context.aws_request_id

    module_name = body['module']
    function_name = body['function']
    args, kwargs = body['args'], body['kwargs']

    logger.debug("Importing module '{}'".format(module_name))
    module = importlib.import_module(module_name, package=None)
    function = getattr(module, function_name)

    logger.debug("Calling function '{}'".format(function_name))
    result = function(*args, **kwargs)
    result_json = json.dumps(result)

    resultData = {
        'RequestId': {'S': request_id},
        'Result': {'S': result_json}
    }

    logger.debug("Creating sockets client")
    apigw_management = boto3.client('apigatewaymanagementapi', endpoint_url=F"https://{domain_name}/{stage}")

    try:
        logger.debug("Send result to websocket")
        _ = apigw_management.post_to_connection(ConnectionId=connection_id,
                                                     Data=json.dumps({"requestId": request_id, "result": result}))
        logger.debug("Sent result to websocket")
    except botocore.exceptions.ClientError as e:
        logger.debug('post_to_connection failed: %s' % e)
        return {'statusCode': 500,
                 'body': 'something went wrong'}

    logger.debug("Storing call result")
    dynamodb.put_item(TableName=os.environ['TABLE_NAME'], Item=resultData)

    return {'statusCode': 418,
             'body': 'ok'}
