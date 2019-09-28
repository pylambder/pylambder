import json
import os
import logging

import boto3
import botocore

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

dynamodb = boto3.client('dynamodb')


def lambda_handler(event, context):
    logger.debug("Task result event: %s" % event)

    request_context = event.get('requestContext', {})

    body = json.loads(event.get('body', '{}'))
    request_id = body.get('RequestId')
    domain_name = request_context.get('domainName')
    stage = request_context.get('stage')
    connection_id = request_context.get('connectionId')
    if (body and stage and request_id and connection_id and domain_name) is None:
        logger.warning("Bad request: {} and {} and {} and {} and {}".format(body, stage, request_id, connection_id, domain_name))
        return { 'statusCode': 400,
                 'body': 'bad request'}

    results = dynamodb.get_item(TableName=os.environ['TABLE_NAME'], Key={'RequestId': {"S": request_id}})
    if results is None:
        return { 'statusCode': 404,
                 'body': 'No results for this task'}

    apigw_management = boto3.client('apigatewaymanagementapi', endpoint_url=F"https://{domain_name}/{stage}")
    if 'Item' in results:
        result = results['Item']
        try:
            _ = apigw_management.post_to_connection(ConnectionId=connection_id,
                                                     Data=json.dumps({"result": json.loads(result['Result']['B'])}))
        except botocore.exceptions.ClientError as e:
            logger.debug('post_to_connection failed: %s' % e)
            return {'statusCode': 500,
                     'body': 'something went wrong'}

    return {'statusCode': 200,
             'body': 'ok'}