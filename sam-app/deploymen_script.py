client = boto3.client('cloudformation')

stackname = ""
templateurl = ""
params = []
capabilities = "CAPABILITY_IAM"

# Helper function to retrieve change set status
def changeSetStatus(change_set_name, client):
    response = client.describe_change_set(
      ChangeSetName=change_set_name,
    )
    return response['Status']

# Create change set
cs_response = client.create_change_set(
  StackName=stackname,
  TemplateBody="""AWSTemplateFormatVersion: "2010-09-09"
Transform: AWS::Serverless-2016-10-31
Description: >
  sam-app

  Sample SAM Template for sam-app

# More info about Globals: https://github.com/awslabs/serverless-application-model/blob/master/docs/globals.rst
Globals:
  Function:
    Timeout: 7

Parameters:
  TableName:
    Type: String
    Default: "task-results"
    Description: (Required) The name of the new DynamoDB to store results.
    MinLength: 3
    MaxLength: 50
    AllowedPattern: ^[A-Za-z_\-]+$

Resources:
  ## Global

  Deployment:
    Type: AWS::ApiGatewayV2::Deployment
    DependsOn:
      - ConnectRoute
      - TaskExecuteRoute
      - TaskResultRoute
      - DisconnectRoute
    Properties:
      ApiId: !Ref TasksWebSocket

  Stage:
    Type: AWS::ApiGatewayV2::Stage
    Properties:
      StageName: Prod
      Description: Prod Stage
      DeploymentId: !Ref Deployment
      ApiId: !Ref TasksWebSocket

  ## Lambda layers

  MainLayer:
    Type: AWS::Serverless::LayerVersion
    Properties:
      LayerName: MainLayer
      Description: Lambda layer with correct boto version ...
      ContentUri: lambda-layers/dependencies-layer.zip
      CompatibleRuntimes:
        - python3.7
      LicenseInfo: MIT
      RetentionPolicy: Retain

  ProjectLayer:
    Type: AWS::Serverless::LayerVersion
    Properties:
      LayerName: ProjectLayer
      Description: Lambda layer with task functions
      ContentUri: lambda-layers/project-layer.zip
      CompatibleRuntimes:
        - python3.7
      LicenseInfo: MIT
      RetentionPolicy: Retain

  ## Storage

  ResultsTable:
    Type: "AWS::Serverless::SimpleTable"
    Properties:
      TableName: !Ref TableName
      PrimaryKey:
        Name: RequestId
        Type: String

  ## API

  TasksWebSocket:
    Type: AWS::ApiGatewayV2::Api
    Properties:
      Name: TasksWebSocket
      ProtocolType: WEBSOCKET
      RouteSelectionExpression: "$request.body.action"

  ## Connect

  ConnectRoute:
    Type: AWS::ApiGatewayV2::Route
    Properties:
      ApiId: !Ref TasksWebSocket
      RouteKey: $connect
      AuthorizationType: NONE
      OperationName: ConnectRoute
      Target: !Join # Join with specified delimiter (here: `/`)
        - "/"
        - - "integrations"
          - !Ref ConnectInteg
  ConnectInteg:
    Type: AWS::ApiGatewayV2::Integration
    Properties:
      ApiId: !Ref TasksWebSocket
      Description: Connect Integration
      IntegrationType: AWS_PROXY
      IntegrationUri:
        Fn::Sub: # Variable interpolation
          arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${OnConnectFunction.Arn}/invocations

  OnConnectFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: onconnect/
      Handler: handler.lambda_handler
      MemorySize: 256
      Runtime: python3.7

  OnConnectPermission:
    Type: AWS::Lambda::Permission
    DependsOn:
      - TasksWebSocket
      - OnConnectFunction
    Properties:
      Action: lambda:InvokeFunction
      FunctionName: !Ref OnConnectFunction
      Principal: apigateway.amazonaws.com

  ## Disconnect

  DisconnectRoute:
    Type: AWS::ApiGatewayV2::Route
    Properties:
      ApiId: !Ref TasksWebSocket
      RouteKey: $disconnect
      AuthorizationType: NONE
      OperationName: DisconnectRoute
      Target: !Join
        - "/"
        - - "integrations"
          - !Ref DisconnectInteg

  DisconnectInteg:
    Type: AWS::ApiGatewayV2::Integration
    Properties:
      ApiId: !Ref TasksWebSocket
      Description: Disconnect Integration
      IntegrationType: AWS_PROXY
      IntegrationUri:
        Fn::Sub: arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${OnDisconnectFunction.Arn}/invocations

  OnDisconnectFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: ondisconnect/
      Handler: handler.lambda_handler
      MemorySize: 256
      Runtime: python3.7

  OnDisconnectPermission:
    Type: AWS::Lambda::Permission
    DependsOn:
      - TasksWebSocket
      - OnDisconnectFunction
    Properties:
      Action: lambda:InvokeFunction
      FunctionName: !Ref OnDisconnectFunction
      Principal: apigateway.amazonaws.com

  ## TaskExecute

  TaskExecuteRoute:
    Type: AWS::ApiGatewayV2::Route
    Properties:
      ApiId: !Ref TasksWebSocket
      RouteKey: execute
      AuthorizationType: NONE
      OperationName: TaskExecuteRoute
      Target: !Join
        - "/"
        - - "integrations"
          - !Ref TaskExecuteInteg

  TaskExecuteInteg:
    Type: AWS::ApiGatewayV2::Integration
    Properties:
      ApiId: !Ref TasksWebSocket
      Description: Execute Integration
      IntegrationType: AWS_PROXY
      IntegrationUri:
        Fn::Sub: arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${TaskExecuteFunction.Arn}/invocations

  TaskExecuteFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: taskexecute/
      Handler: handler.lambda_handler
      MemorySize: 256
      Runtime: python3.7
      Environment:
        Variables:
          TABLE_NAME: !Ref TableName
          DIR_NAME: taskexecute
      Policies:
        - DynamoDBCrudPolicy:
            TableName: !Ref TableName
        - Statement:
            - Effect: Allow
              Action:
                - "execute-api:ManageConnections"
              Resource:
                - !Sub "arn:aws:execute-api:${AWS::Region}:${AWS::AccountId}:${TasksWebSocket}/*"
      Layers:
        - !Ref MainLayer
        - !Ref ProjectLayer

  TaskExecutePermission:
    Type: AWS::Lambda::Permission
    DependsOn:
      - TasksWebSocket
      - TaskExecuteFunction
    Properties:
      Action: lambda:InvokeFunction
      FunctionName: !Ref TaskExecuteFunction
      Principal: apigateway.amazonaws.com

  ## TaskResult

  TaskResultRoute:
    Type: AWS::ApiGatewayV2::Route
    Properties:
      ApiId: !Ref TasksWebSocket
      RouteKey: result
      AuthorizationType: NONE
      OperationName: TaskResultRoute
      Target: !Join
        - "/"
        - - "integrations"
          - !Ref TaskResultInteg
  TaskResultInteg:
    Type: AWS::ApiGatewayV2::Integration
    Properties:
      ApiId: !Ref TasksWebSocket
      Description: Result Integration
      IntegrationType: AWS_PROXY
      IntegrationUri:
        Fn::Sub: arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${TaskResultFunction.Arn}/invocations

  TaskResultFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: taskresult/
      Handler: handler.lambda_handler
      MemorySize: 256
      Runtime: python3.7
      Environment:
        Variables:
          TABLE_NAME: !Ref TableName
          DIR_NAME: taskresult
      Policies:
        - DynamoDBCrudPolicy:
            TableName: !Ref TableName
        - Statement:
            - Effect: Allow
              Action:
                - "execute-api:ManageConnections"
              Resource:
                - !Sub "arn:aws:execute-api:${AWS::Region}:${AWS::AccountId}:${TasksWebSocket}/*"
      Layers:
        - !Ref MainLayer

  TaskResultPermission:
    Type: AWS::Lambda::Permission
    DependsOn:
      - TasksWebSocket
      - TaskResultFunction
    Properties:
      Action: lambda:InvokeFunction
      FunctionName: !Ref TaskResultFunction
      Principal: apigateway.amazonaws.com

Outputs:
  ResultsTableArn:
    Description: "Connections table ARN"
    Value: !GetAtt ResultsTable.Arn

  OnConnectFunctionArn:
    Description: "OnConnect function ARN"
    Value: !GetAtt OnConnectFunction.Arn

  OnDisconnectFunctionArn:
    Description: "OnDisconnect function ARN"
    Value: !GetAtt OnDisconnectFunction.Arn

  TaskExecuteFunctionArn:
    Description: "TaskExecute function ARN"
    Value: !GetAtt TaskExecuteFunction.Arn

  TaskResultFunctionArn:
    Description: "TaskResult function ARN"
    Value: !GetAtt TaskResultFunction.Arn

  MainLayerARN:
    Value: !Ref MainLayer
    Description: MainLayer ARN
    Export:
      Name: main-layer-arn

  ProjectLayerARN:
    Value: !Ref ProjectLayer
    Description: ProjectLayer ARN
    Export:
      Name: project-layer-arn

  WebSocketURI:
    Description: "The WSS Protocol URI to connect to"
    Value:
      !Join [
        "",
        [
          "wss://",
          !Ref TasksWebSocket,
          ".execute-api.",
          !Ref "AWS::Region",
          ".amazonaws.com/",
          !Ref "Stage",
        ],
      ]

  """,
  Parameters=params,
  Capabilities=[capabilities],
  ChangeSetType="CREATE",
  ChangeSetName=stackname + "-cs"
)

change_set_name = cs_response['Id']

# Wait until change set status is CREATE_COMPLETE
while True:
  response = change_set_status(change_set_name, client)
  print(str(response))
  time.sleep(10)
  if response == 'CREATE_COMPLETE':
      break

# Execute change set
ex_response = client.execute_change_set(
  ChangeSetName=change_set_name
)