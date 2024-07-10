import json
import boto3
import os

dynamodb = boto3.resource('dynamodb')
groups_table = dynamodb.Table(os.environ['GROUPS_TABLE_NAME'])

def handler(event, context):
    body = json.loads(event['body'])
    group_id = body['groupId']
    user_id = body['userId']

    try:
        response = groups_table.update_item(
            Key={'groupId': group_id},
            UpdateExpression='SET members = list_append(if_not_exists(members, :empty_list), :userId)',
            ExpressionAttributeValues={
                ':userId': [user_id],
                ':empty_list': []
            },
            ReturnValues='UPDATED_NEW'
        )

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'User added to group successfully',
                'groupId': group_id,
                'userId': user_id
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Internal server error',
                'error': str(e)
            })
        }
