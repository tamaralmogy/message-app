import json
import uuid
import boto3
import os

dynamodb = boto3.resource('dynamodb')
messages_table = dynamodb.Table(os.environ['MESSAGES_TABLE_NAME'])
groups_table = dynamodb.Table(os.environ['GROUPS_TABLE_NAME'])

def handler(event, context):
    try:
        body = json.loads(event['body'])
        sender_id = body['senderId']
        group_id = body['groupId']
        content = body['content']
        
        # Fetch group details
        group_response = groups_table.get_item(Key={'groupId': group_id})
        
        if 'Item' not in group_response:
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'Group not found'})
            }
        
        group = group_response['Item']
        members = group.get('members', [])
        
        if not members:
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'Group has no members'})
            }
        
        # Send message to each member
        message_id = str(uuid.uuid4())
        timestamp = body.get('timestamp', '')
        for member_id in members:
            message = {
                'messageId': message_id,
                'senderId': sender_id,
                'recipientId': member_id,
                'groupId': group_id,
                'content': content,
                'timestamp': timestamp
            }
            messages_table.put_item(Item=message)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Message sent to group successfully',
                'messageId': message_id
            })
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Internal server error', 'error': str(e)})
        }
