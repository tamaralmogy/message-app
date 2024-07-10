import json
import boto3
import os

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['USERS_TABLE_NAME'])

def handler(event, context):
    body = json.loads(event['body'])
    blocker_id = body['blockerId']
    blocked_id = body['blockedId']

    # Update the block list for the blocker
    response = table.update_item(
        Key={
            'userId': blocker_id
        },
        UpdateExpression="ADD blockedUsers :blockedUser",
        ExpressionAttributeValues={
            ':blockedUser': {blocked_id}
        }
    )

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'User blocked successfully',
            'blockerId': blocker_id,
            'blockedId': blocked_id
        })
    }
