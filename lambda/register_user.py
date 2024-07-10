import json
import uuid
import boto3
import os

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['USERS_TABLE_NAME'])

def handler(event, context):
    http_method = event['httpMethod']
    try:
        if http_method == 'POST':
            body = json.loads(event['body'])

            # Check if required keys are present
            if 'name' not in body or 'email' not in body:
                raise KeyError('Missing required key in request body: name or email')

            user_id = str(uuid.uuid4())
            user = {
                'userId': user_id,
                'name': body['name'],
                'email': body['email']
            }
            table.put_item(Item=user)
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'User registered successfully',
                    'userId': user_id
                })
            }

        elif http_method == 'DELETE':
            body = json.loads(event['body'])

            # Check if required key is present
            if 'userId' not in body:
                raise KeyError('Missing required key in request body: userId')

            user_id = body['userId']
            table.delete_item(Key={'userId': user_id})
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'User deleted successfully',
                    'userId': user_id
                })
            }

        else:
            return {
                'statusCode': 405,
                'body': json.dumps({
                    'message': 'Method Not Allowed'
                })
            }
    except KeyError as e:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': str(e)
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
