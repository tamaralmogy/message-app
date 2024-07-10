import json
import boto3
import os
import logging

dynamodb = boto3.resource('dynamodb')
messages_table = dynamodb.Table(os.environ['MESSAGES_TABLE_NAME'])

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        body = json.loads(event['body'])
        user_id = body['userId']
        
        response = messages_table.scan(
            FilterExpression='recipientId = :recipientId',
            ExpressionAttributeValues={':recipientId': user_id}
        )
        
        messages = response.get('Items', [])
        
        if not messages:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'No messages found for this user.'
                })
            }
        
        return {
            'statusCode': 200,
            'body': json.dumps(messages)
        }
    except Exception as e:
        logger.error(f"Error checking messages: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Internal server error',
                'error': str(e)
            })
        }
