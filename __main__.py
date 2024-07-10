import pulumi
from pulumi_aws import lambda_, apigateway, iam, dynamodb, cloudwatch

# Create a DynamoDB table for users
users_table = dynamodb.Table('users-table',
    attributes=[{
        'name': 'userId',
        'type': 'S',
    }],
    hash_key='userId',
    billing_mode='PAY_PER_REQUEST'
)

# Create a DynamoDB table for messages
messages_table = dynamodb.Table('messages-table',
    attributes=[{
        'name': 'messageId',
        'type': 'S',
    }],
    hash_key='messageId',
    billing_mode='PAY_PER_REQUEST'
)

# Create a DynamoDB table for groups
groups_table = dynamodb.Table('groups-table',
    attributes=[{
        'name': 'groupId',
        'type': 'S',
    }],
    hash_key='groupId',
    billing_mode='PAY_PER_REQUEST'
)

# Create an IAM role for Lambda
role = iam.Role('lambda-exec-role',
    assume_role_policy="""{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "lambda.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }"""
)

# Attach the basic execution role policy
role_policy = iam.RolePolicyAttachment('lambda-role-policy',
    role=role.name,
    policy_arn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
)

# Create a policy to allow access to DynamoDB
dynamodb_policy_document = pulumi.Output.all(users_table.arn, messages_table.arn, groups_table.arn).apply(lambda arns: f"""{{
    "Version": "2012-10-17",
    "Statement": [
        {{
            "Effect": "Allow",
            "Action": [
                "dynamodb:PutItem",
                "dynamodb:DeleteItem",
                "dynamodb:UpdateItem",
                "dynamodb:GetItem",
                "dynamodb:Scan"  
            ],
            "Resource": "{arns[0]}"
        }},
        {{
            "Effect": "Allow",
            "Action": [
                "dynamodb:PutItem",
                "dynamodb:UpdateItem",
                "dynamodb:GetItem",
                "dynamodb:Scan"  
            ],
            "Resource": "{arns[1]}"
        }},
        {{
            "Effect": "Allow",
            "Action": [
                "dynamodb:PutItem",
                "dynamodb:UpdateItem",
                "dynamodb:GetItem",
                "dynamodb:Scan"  
            ],
            "Resource": "{arns[2]}"
        }}
    ]
}}""")

dynamodb_policy = iam.Policy('dynamodb-access-policy',
    policy=dynamodb_policy_document
)

# Attach the DynamoDB policy to the role
dynamodb_policy_attachment = iam.RolePolicyAttachment('dynamodb-policy-attachment',
    role=role.name,
    policy_arn=dynamodb_policy.arn
)

# Create the user management Lambda function
user_lambda_function = lambda_.Function('user-function',
    runtime='python3.8',
    role=role.arn,
    handler='register_user.handler',
    code=pulumi.AssetArchive({
        '.': pulumi.FileArchive('./lambda')
    }),
    environment={
        'variables': {
            'USERS_TABLE_NAME': users_table.name
        }
    }
)

# Create the send message Lambda function
send_message_lambda = lambda_.Function('send-message-function',
    runtime='python3.8',
    role=role.arn,
    handler='send_message.handler',
    code=pulumi.AssetArchive({
        '.': pulumi.FileArchive('./lambda')
    }),
    environment={
        'variables': {
            'MESSAGES_TABLE_NAME': messages_table.name,
            'USERS_TABLE_NAME': users_table.name  # Added to check if the user is blocked
        }
    }
)

# Create the block user Lambda function
block_user_lambda = lambda_.Function('block-user-function',
    runtime='python3.8',
    role=role.arn,
    handler='block_user.handler',
    code=pulumi.AssetArchive({
        '.': pulumi.FileArchive('./lambda')
    }),
    environment={
        'variables': {
            'USERS_TABLE_NAME': users_table.name
        }
    }
)

# Create the create group Lambda function
create_group_lambda = lambda_.Function('create-group-function',
    runtime='python3.8',
    role=role.arn,
    handler='create_group.handler',
    code=pulumi.AssetArchive({
        '.': pulumi.FileArchive('./lambda')
    }),
    environment={
        'variables': {
            'GROUPS_TABLE_NAME': groups_table.name
        }
    }
)

# Create the send group message Lambda function
send_group_message_lambda = lambda_.Function('send-group-message-function',
    runtime='python3.8',
    role=role.arn,
    handler='send_group_message.handler',
    code=pulumi.AssetArchive({
        '.': pulumi.FileArchive('./lambda')
    }),
    environment={
        'variables': {
            'MESSAGES_TABLE_NAME': messages_table.name,
            'GROUPS_TABLE_NAME': groups_table.name
        }
    }
)

# Create a CloudWatch log group
log_group = cloudwatch.LogGroup('api-gateway-log-group',
    retention_in_days=7
)

# Create a CloudWatch Logs role for API Gateway
cloudwatch_logs_role = iam.Role('api-gateway-cloudwatch-logs-role',
    assume_role_policy="""{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "apigateway.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }"""
)

cloudwatch_logs_policy_attachment = iam.RolePolicyAttachment('cloudwatch-logs-policy-attachment',
    role=cloudwatch_logs_role.name,
    policy_arn='arn:aws:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs'
)

# Create an API Gateway
api = apigateway.RestApi('user-api',
    description='API for User Management Lambda'
)

# Ensure the API is created before creating the resource by applying the ID
api_root_resource_id = api.root_resource_id.apply(lambda id: id)

# Create the /register resource
register_resource = apigateway.Resource('register-resource',
    rest_api=api.id,
    parent_id=api_root_resource_id,
    path_part='register',
    opts=pulumi.ResourceOptions(depends_on=[api])
)

# Define a POST method on the /register resource
register_method_post = apigateway.Method('register-method-post',
    rest_api=api.id,
    resource_id=register_resource.id,
    http_method='POST',
    authorization='NONE',
    opts=pulumi.ResourceOptions(depends_on=[register_resource])
)

# Set up the Lambda integration for the POST method
register_integration_post = apigateway.Integration('register-integration-post',
    rest_api=api.id,
    resource_id=register_resource.id,
    http_method=register_method_post.http_method,
    integration_http_method='POST',
    type='AWS_PROXY',
    uri=user_lambda_function.invoke_arn,
    opts=pulumi.ResourceOptions(depends_on=[register_method_post])
)

# Define a DELETE method on the /register resource
register_method_delete = apigateway.Method('register-method-delete',
    rest_api=api.id,
    resource_id=register_resource.id,
    http_method='DELETE',
    authorization='NONE',
    opts=pulumi.ResourceOptions(depends_on=[register_resource])
)

# Set up the Lambda integration for the DELETE method
register_integration_delete = apigateway.Integration('register-integration-delete',
    rest_api=api.id,
    resource_id=register_resource.id,
    http_method=register_method_delete.http_method,
    integration_http_method='POST',
    type='AWS_PROXY',
    uri=user_lambda_function.invoke_arn,
    opts=pulumi.ResourceOptions(depends_on=[register_method_delete])
)

# Create the /message resource
message_resource = apigateway.Resource('message-resource',
    rest_api=api.id,
    parent_id=api_root_resource_id,
    path_part='message',
    opts=pulumi.ResourceOptions(depends_on=[api])
)

# Define a POST method on the /message resource
message_method_post = apigateway.Method('message-method-post',
    rest_api=api.id,
    resource_id=message_resource.id,
    http_method='POST',
    authorization='NONE',
    opts=pulumi.ResourceOptions(depends_on=[message_resource])
)

# Set up the Lambda integration for the POST method on /message
message_integration_post = apigateway.Integration('message-integration-post',
    rest_api=api.id,
    resource_id=message_resource.id,
    http_method=message_method_post.http_method,
    integration_http_method='POST',
    type='AWS_PROXY',
    uri=send_message_lambda.invoke_arn,
    opts=pulumi.ResourceOptions(depends_on=[message_method_post])
)

# Create the /block resource
block_resource = apigateway.Resource('block-resource',
    rest_api=api.id,
    parent_id=api_root_resource_id,
    path_part='block',
    opts=pulumi.ResourceOptions(depends_on=[api])
)

# Define a POST method on the /block resource
block_method_post = apigateway.Method('block-method-post',
    rest_api=api.id,
    resource_id=block_resource.id,
    http_method='POST',
    authorization='NONE',
    opts=pulumi.ResourceOptions(depends_on=[block_resource])
)

# Set up the Lambda integration for the POST method on /block
block_integration_post = apigateway.Integration('block-integration-post',
    rest_api=api.id,
    resource_id=block_resource.id,
    http_method=block_method_post.http_method,
    integration_http_method='POST',
    type='AWS_PROXY',
    uri=block_user_lambda.invoke_arn,
    opts=pulumi.ResourceOptions(depends_on=[block_method_post])
)

# Create the /group resource
group_resource = apigateway.Resource('group-resource',
    rest_api=api.id,
    parent_id=api_root_resource_id,
    path_part='group',
    opts=pulumi.ResourceOptions(depends_on=[api])
)

# Define a POST method on the /group resource
group_method_post = apigateway.Method('group-method-post',
    rest_api=api.id,
    resource_id=group_resource.id,
    http_method='POST',
    authorization='NONE',
    opts=pulumi.ResourceOptions(depends_on=[group_resource])
)

# Set up the Lambda integration for the POST method on /group
group_integration_post = apigateway.Integration('group-integration-post',
    rest_api=api.id,
    resource_id=group_resource.id,
    http_method=group_method_post.http_method,
    integration_http_method='POST',
    type='AWS_PROXY',
    uri=create_group_lambda.invoke_arn,
    opts=pulumi.ResourceOptions(depends_on=[group_method_post])
)

# Create the /group/message resource
group_message_resource = apigateway.Resource('group-message-resource',
    rest_api=api.id,
    parent_id=group_resource.id,
    path_part='message',
    opts=pulumi.ResourceOptions(depends_on=[group_resource])
)

# Define a POST method on the /group/message resource
group_message_method_post = apigateway.Method('group-message-method-post',
    rest_api=api.id,
    resource_id=group_message_resource.id,
    http_method='POST',
    authorization='NONE',
    opts=pulumi.ResourceOptions(depends_on=[group_message_resource])
)

# Set up the Lambda integration for the POST method on /group/message
group_message_integration_post = apigateway.Integration('group-message-integration-post',
    rest_api=api.id,
    resource_id=group_message_resource.id,
    http_method=group_message_method_post.http_method,
    integration_http_method='POST',
    type='AWS_PROXY',
    uri=send_group_message_lambda.invoke_arn,
    opts=pulumi.ResourceOptions(depends_on=[group_message_method_post])
)
# Create the add user to group Lambda function
add_user_to_group_lambda = lambda_.Function('add-user-to-group-function',
    runtime='python3.8',
    role=role.arn,
    handler='add_user_to_group.handler',
    code=pulumi.AssetArchive({
        '.': pulumi.FileArchive('./lambda')
    }),
    environment={
        'variables': {
            'GROUPS_TABLE_NAME': groups_table.name
        }
    }
)

# Create the /group/add-user resource
add_user_resource = apigateway.Resource('add-user-resource',
    rest_api=api.id,
    parent_id=group_resource.id,
    path_part='add-user',
    opts=pulumi.ResourceOptions(depends_on=[group_resource])
)

# Define a POST method on the /group/add-user resource
add_user_method_post = apigateway.Method('add-user-method-post',
    rest_api=api.id,
    resource_id=add_user_resource.id,
    http_method='POST',
    authorization='NONE',
    opts=pulumi.ResourceOptions(depends_on=[add_user_resource])
)

# Set up the Lambda integration for the POST method on /group/add-user
add_user_integration_post = apigateway.Integration('add-user-integration-post',
    rest_api=api.id,
    resource_id=add_user_resource.id,
    http_method=add_user_method_post.http_method,
    integration_http_method='POST',
    type='AWS_PROXY',
    uri=add_user_to_group_lambda.invoke_arn,
    opts=pulumi.ResourceOptions(depends_on=[add_user_method_post])
)
# Create the remove user from group Lambda function
remove_user_from_group_lambda = lambda_.Function('remove-user-from-group-function',
    runtime='python3.8',
    role=role.arn,
    handler='remove_user_from_group.handler',
    code=pulumi.AssetArchive({
        '.': pulumi.FileArchive('./lambda')
    }),
    environment={
        'variables': {
            'GROUPS_TABLE_NAME': groups_table.name
        }
    }
)

# Create the /group/remove-user resource
remove_user_resource = apigateway.Resource('remove-user-resource',
    rest_api=api.id,
    parent_id=group_resource.id,
    path_part='remove-user',
    opts=pulumi.ResourceOptions(depends_on=[group_resource])
)

# Define a POST method on the /group/remove-user resource
remove_user_method_post = apigateway.Method('remove-user-method-post',
    rest_api=api.id,
    resource_id=remove_user_resource.id,
    http_method='POST',
    authorization='NONE',
    opts=pulumi.ResourceOptions(depends_on=[remove_user_resource])
)

# Set up the Lambda integration for the POST method on /group/remove-user
remove_user_integration_post = apigateway.Integration('remove-user-integration-post',
    rest_api=api.id,
    resource_id=remove_user_resource.id,
    http_method=remove_user_method_post.http_method,
    integration_http_method='POST',
    type='AWS_PROXY',
    uri=remove_user_from_group_lambda.invoke_arn,
    opts=pulumi.ResourceOptions(depends_on=[remove_user_method_post])
)

# Create the check messages Lambda function
check_messages_lambda = lambda_.Function('check-messages-function',
    runtime='python3.8',
    role=role.arn,
    handler='check_messages.handler',
    code=pulumi.AssetArchive({
        '.': pulumi.FileArchive('./lambda')
    }),
    environment={
        'variables': {
            'MESSAGES_TABLE_NAME': messages_table.name
        }
    }
)

# Create the /messages resource
messages_resource = apigateway.Resource('messages-resource',
    rest_api=api.id,
    parent_id=api_root_resource_id,
    path_part='messages',
    opts=pulumi.ResourceOptions(depends_on=[api])
)

# Define a POST method on the /messages resource
messages_method_post = apigateway.Method('messages-method-post',
    rest_api=api.id,
    resource_id=messages_resource.id,
    http_method='POST',
    authorization='NONE',
    opts=pulumi.ResourceOptions(depends_on=[messages_resource])
)

# Set up the Lambda integration for the POST method on /messages
messages_integration_post = apigateway.Integration('messages-integration-post',
    rest_api=api.id,
    resource_id=messages_resource.id,
    http_method=messages_method_post.http_method,
    integration_http_method='POST',
    type='AWS_PROXY',
    uri=check_messages_lambda.invoke_arn,
    opts=pulumi.ResourceOptions(depends_on=[messages_method_post])
)

# Add permission for API Gateway to invoke the check messages Lambda function
check_messages_lambda_permission = lambda_.Permission('check-messages-permission',
    action='lambda:InvokeFunction',
    function=check_messages_lambda.name,
    principal='apigateway.amazonaws.com',
    source_arn=api.execution_arn.apply(lambda arn: f"{arn}/*/*/*")
)

# Add permission for API Gateway to invoke the remove user from group Lambda function
remove_user_from_group_lambda_permission = lambda_.Permission('remove-user-from-group-permission',
    action='lambda:InvokeFunction',
    function=remove_user_from_group_lambda.name,
    principal='apigateway.amazonaws.com',
    source_arn=api.execution_arn.apply(lambda arn: f"{arn}/*/*/*")
)

# Add permission for API Gateway to invoke the add user to group Lambda function
add_user_to_group_lambda_permission = lambda_.Permission('add-user-to-group-permission',
    action='lambda:InvokeFunction',
    function=add_user_to_group_lambda.name,
    principal='apigateway.amazonaws.com',
    source_arn=api.execution_arn.apply(lambda arn: f"{arn}/*/*/*")
)

# Add permission for API Gateway to invoke the user Lambda function
user_lambda_permission = lambda_.Permission('user-permission',
    action='lambda:InvokeFunction',
    function=user_lambda_function.name,
    principal='apigateway.amazonaws.com',
    source_arn=api.execution_arn.apply(lambda arn: f"{arn}/*/*/*")
)

# Add permission for API Gateway to invoke the send message Lambda function
send_message_lambda_permission = lambda_.Permission('send-message-permission',
    action='lambda:InvokeFunction',
    function=send_message_lambda.name,
    principal='apigateway.amazonaws.com',
    source_arn=api.execution_arn.apply(lambda arn: f"{arn}/*/*/*")
)

# Add permission for API Gateway to invoke the block user Lambda function
block_user_lambda_permission = lambda_.Permission('block-user-permission',
    action='lambda:InvokeFunction',
    function=block_user_lambda.name,
    principal='apigateway.amazonaws.com',
    source_arn=api.execution_arn.apply(lambda arn: f"{arn}/*/*/*")
)

# Add permission for API Gateway to invoke the create group Lambda function
create_group_lambda_permission = lambda_.Permission('create-group-permission',
    action='lambda:InvokeFunction',
    function=create_group_lambda.name,
    principal='apigateway.amazonaws.com',
    source_arn=api.execution_arn.apply(lambda arn: f"{arn}/*/*/*")
)

# Add permission for API Gateway to invoke the send group message Lambda function
send_group_message_lambda_permission = lambda_.Permission('send-group-message-permission',
    action='lambda:InvokeFunction',
    function=send_group_message_lambda.name,
    principal='apigateway.amazonaws.com',
    source_arn=api.execution_arn.apply(lambda arn: f"{arn}/*/*/*")
)

# Update the deployment to include the new endpoints
deployment = apigateway.Deployment('user-deployment',
    rest_api=api.id,
    stage_name='dev',
    opts=pulumi.ResourceOptions(depends_on=[
        register_integration_post, register_integration_delete,
        message_integration_post, block_integration_post,
        group_integration_post, group_message_integration_post,
        add_user_integration_post, remove_user_integration_post,
        messages_integration_post,  # Add this line
        user_lambda_permission, send_message_lambda_permission,
        block_user_lambda_permission, create_group_lambda_permission,
        send_group_message_lambda_permission, add_user_to_group_lambda_permission,
        remove_user_from_group_lambda_permission, check_messages_lambda_permission  # Add this line
    ])
)

# Enable CloudWatch Logs for the API Gateway stage
api_stage = apigateway.Stage('dev-stage',
    rest_api=api.id,
    deployment=deployment.id,
    stage_name='dev',
    description='Dev stage',
    access_log_settings={
        'destination_arn': log_group.arn,
        'format': '$context.requestId $context.identity.sourceIp $context.identity.userAgent $context.requestTime $context.httpMethod $context.resourcePath $context.status $context.protocol'
    },
    variables={
        'log_level': 'INFO'
    },
    opts=pulumi.ResourceOptions(ignore_changes=["stage_name"])
)

# Export the URLs of the API Gateway
pulumi.export('role_arn', role.arn)
pulumi.export('user_lambda_function_arn', user_lambda_function.arn)
pulumi.export('send_message_lambda_arn', send_message_lambda.arn)
pulumi.export('block_user_lambda_arn', block_user_lambda.arn)
pulumi.export('create_group_lambda_arn', create_group_lambda.arn)
pulumi.export('send_group_message_lambda_arn', send_group_message_lambda.arn)
pulumi.export('register_url', deployment.invoke_url.apply(lambda invoke_url: f"{invoke_url}/register"))
pulumi.export('message_url', deployment.invoke_url.apply(lambda invoke_url: f"{invoke_url}/message"))
pulumi.export('block_url', deployment.invoke_url.apply(lambda invoke_url: f"{invoke_url}/block"))
pulumi.export('group_url', deployment.invoke_url.apply(lambda invoke_url: f"{invoke_url}/group"))
pulumi.export('group_message_url', deployment.invoke_url.apply(lambda invoke_url: f"{invoke_url}/group/message"))
pulumi.export('users_table_name', users_table.name)
pulumi.export('messages_table_name', messages_table.name)
pulumi.export('groups_table_name', groups_table.name)
pulumi.export('add_user_to_group_url', deployment.invoke_url.apply(lambda invoke_url: f"{invoke_url}/group/add-user"))
pulumi.export('remove_user_from_group_url', deployment.invoke_url.apply(lambda invoke_url: f"{invoke_url}/group/remove-user"))
pulumi.export('check_messages_url', deployment.invoke_url.apply(lambda invoke_url: f"{invoke_url}/messages"))  # Add this line
