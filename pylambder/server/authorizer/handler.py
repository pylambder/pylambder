import logging
import os

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def lambda_handler(event, context):
    logger.info(F"Event: {event}")
    logger.info(F"Context: {context}")
    # Retrieve request parameters from the Lambda function input:
    token = event['queryStringParameters']['token']
    expected_token = os.environ['API_TOKEN']
    # Perform authorization to return the Allow policy for correct parameters and
    # the 'Unauthorized' error, otherwise.
    if token == expected_token:
        return generate_allow('me', event["methodArn"])
    else:
        return generate_deny('me', event["methodArn"])


# Help function to generate an IAM policy
def generate_policy(principalId, effect, resource):
    # Required output:
    auth_response = {"principalId": principalId};
    if effect and resource:
        policy_document = {}
        policy_document["Version"] = '2012-10-17';  # default version
        policy_document["Statement"] = []
        statement_one = {}
        statement_one["Action"] = 'execute-api:Invoke'
        statement_one["Effect"] = effect
        statement_one["Resource"] = resource
        policy_document["Statement"].append(statement_one)
        auth_response["policyDocument"] = policy_document;

    return auth_response;


def generate_allow(principalId, resource):
    return generate_policy(principalId, 'Allow', resource);


def generate_deny(principalId, resource):
    return generate_policy(principalId, 'Deny', resource);
