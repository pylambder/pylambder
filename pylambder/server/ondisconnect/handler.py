import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def lambda_handler(event, context):
    logger.debug("Disconnected event: %s" % event)

    connection_id = event.get('requestContext', {}).get('connectionId')
    if connection_id is None:
        return { 'statusCode': 400,
                 'body': 'bad request' }

    return { 'statusCode': 200,
             'body': 'ok' }