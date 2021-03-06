import json

import boto3


def main(event, context):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('CSE4940UsersTable')
    result = table.scan(Select="ALL_ATTRIBUTES")
    return result["Items"]
