import json
import uuid
import boto3
import os

dynamodb = boto3.resource('dynamodb')
messages_table = dynamodb.Table(os.environ['MESSAGES_TABLE_NAME'])
users_table = dynamodb.Table(os.environ['USERS_TABLE_NAME'])

def handler(event, context):
    body = json.loads(event['body'])
    sender_id = body['senderId']
    recipient_id = body['recipientId']
    
    # Check if the sender is blocked by the recipient
    response = users_table.get_item(
        Key={'userId': recipient_id}
    )
    recipient = response.get('Item')
    
    if recipient and 'blockedUsers' in recipient and sender_id in recipient['blockedUsers']:
        return {
            'statusCode': 403,
            'body': json.dumps({
                'message': 'You are blocked from sending messages to this user.'
            })
        }
    
    # If not blocked, proceed to send the message
    message_id = str(uuid.uuid4())
    message = {
        'messageId': message_id,
        'senderId': sender_id,
        'recipientId': recipient_id,
        'content': body['content'],
        'timestamp': body.get('timestamp', '')
    }
    messages_table.put_item(Item=message)
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Message sent successfully',
            'messageId': message_id
        })
    }
