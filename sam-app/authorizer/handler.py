import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def lambda_handler(event, context, callback):
    # Retrieve request parameters from the Lambda function input:
    headers = event.headers;
    queryStringParameters = event.queryStringParameters;
    stageVariables = event.stageVariables;
    requestContext = event.requestContext;
       
    # Parse the input for the parameter values
    tmp = event.methodArn.split(':');
    apiGatewayArnTmp = tmp[5].split('/');
    awsAccountId = tmp[4];
    region = tmp[3];
    restApiId = apiGatewayArnTmp[0];
    stage = apiGatewayArnTmp[1];
    route = apiGatewayArnTmp[2];
       
   # Perform authorization to return the Allow policy for correct parameters and 
   # the 'Unauthorized' error, otherwise.
    if headers.Auth == "test":
        callback(None, generateAllow('me', event.methodArn));
    else:
        callback("Unauthorized");

    
#Help function to generate an IAM policy
def generatePolicy(principalId, effect, resource):
    # Required output:
    authResponse = {};
    authResponse.principalId = principalId;
    if effect and resource:
        policyDocument = {};
        policyDocument.Version = '2012-10-17'; # default version
        policyDocument.Statement = [];
        statementOne = {};
        statementOne["Action"] = 'execute-api:Invoke'; # default action
        statementOne["Effect"] = effect;
        statementOne["Resource"] = resource;
        policyDocument["Statement"][0] = statementOne;
        authResponse.policyDocument = policyDocument;

    return authResponse;
    
def generateAllow(principalId, resource):
    return generatePolicy(principalId, 'Allow', resource);
    
def generateDeny(principalId, resource):
    return generatePolicy(principalId, 'Deny', resource);