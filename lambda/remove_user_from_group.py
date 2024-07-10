import json
import boto3
import os

dynamodb = boto3.resource('dynamodb')
groups_table = dynamodb.Table(os.environ['GROUPS_TABLE_NAME'])

def handler(event, context):
    try:
        # Log the incoming event for debugging
        print("Received event:", event)
        
        body = json.loads(event['body'])
        group_id = body['groupId']
        user_id = body['userId']
        
        # Log the parsed body for debugging
        print("Parsed body:", body)
        
        # Retrieve the current members
        response = groups_table.get_item(Key={'groupId': group_id})
        
        # Log the response from DynamoDB
        print("DynamoDB get_item response:", response)
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'body': json.dumps({
                    'message': 'Group not found',
                    'groupId': group_id
                })
            }
        
        # Extract members list correctly
        members = response['Item'].get('members', [])
        
        # Log the current members for debugging
        print("Current members:", members)
        
        # Filter out the user to be removed
        updated_members = [member for member in members if member != user_id]
        
        # Log the updated members for debugging
        print("Updated members:", updated_members)
        
        # Update the group with the new list of members
        response = groups_table.update_item(
            Key={'groupId': group_id},
            UpdateExpression="SET members = :updated_members",
            ExpressionAttributeValues={':updated_members': updated_members}
        )
        
        # Log the update response for debugging
        print("DynamoDB update_item response:", response)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'User removed from group successfully',
                'groupId': group_id,
                'userId': user_id
            })
        }
    except Exception as e:
        # Log the exception for debugging
        print("Exception:", str(e))
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Internal server error',
                'error': str(e)
            })
        }
