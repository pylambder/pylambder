import json
import os
import logging

import importlib
import time

import boto3
import botocore

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    logger.debug("Task result event: %s" % event)

    request_context = event.get('requestContext', {})

    data = json.loads(event.get('body', '{}')).get('data')
    request_id = event.get('requestId')
    domain_name = request_context.get('domainName')
    stage = request_context.get('stage')
    connection_id = request_context.get('connectionId')
    if (data and domain_name and stage and request_id and connection_id) is None:
        return { 'statusCode': 400,
                 'body': 'bad request'}

    request_id = context.aws_request_id

    module_name = data['module']
    function_name = data['function']
    args, kwargs = data['args'], data['kwargs']

    module = importlib.import_module(module_name, package=None)
    function = getattr(module, function_name)
    result = function(*args, **kwargs)
    result_json = json.dumps(result)

    resultData = {
        'RequestId': {'S': request_id},
        'Result': {'B': result_json}
    }

    dynamodb.put_item(TableName=os.environ['TABLE_NAME'], Item=resultData)

    apigw_management = boto3.client('apigatewaymanagementapi', endpoint_url=F"https://{domain_name}/{stage}")

    try:
        _ = apigw_management.post_to_connection(ConnectionId=connection_id,
                                                     Data=json.dumps({"requestId": request_id}))
    except botocore.exceptions.ClientError as e:
        logger.debug('post_to_connection failed: %s' % e)
        return {'statusCode': 500,
                 'body': 'something went wrong'}

    return {'statusCode': 200,
             'body': 'ok'}