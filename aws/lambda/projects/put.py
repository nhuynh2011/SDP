import boto3
from boto3.dynamodb.conditions import Key


def main(event, context):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('ProjectsTable')
    required = ['id', 'name', 'owner', 'description', 'version', 'template']

    if False in [k in event.keys() for k in required]:
        return {
            'error': 'Missing a required key'
        }

    result = table.update_item(
        Key={
            'id': event['id']
        },
        ExpressionAttributeNames={
            '#n': 'name',
            '#o': 'owner',
            '#d': 'description',
            '#v': 'version',
            '#t': 'template',
        },
        ExpressionAttributeValues={
            ':n': event['name'],
            ':o': event['owner'],
            ':d': event['description'],
            ':v': event['version'],
            ':t': event['template']
        },
        UpdateExpression='SET #n = :n, #o = :o, #d = :d, #v = :v, #t = :t'
    )
    
    result = table.query(
        KeyConditionExpression=Key('id').eq(event['id'])
    )

    return result["Items"][0]