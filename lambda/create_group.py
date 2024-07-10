import json
import uuid
import boto3
import os

dynamodb = boto3.resource('dynamodb')
groups_table = dynamodb.Table(os.environ['GROUPS_TABLE_NAME'])

def handler(event, context):
    body = json.loads(event['body'])
    group_id = str(uuid.uuid4())
    group = {
        'groupId': group_id,
        'groupName': body['groupName'],
        'members': body['members']  # Expecting a list of user IDs
    }
    groups_table.put_item(Item=group)
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Group created successfully',
            'groupId': group_id
        })
    }
