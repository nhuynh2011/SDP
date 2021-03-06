#!/usr/bin/env python3
import argparse
import itertools
import pathlib
import sys

import boto3
import botocore

import client
from template import LambdaParams, Template
import utils

THIS_DIR = pathlib.Path(__file__).parent.absolute()


if __name__ == '__main__':
    my_parser = argparse.ArgumentParser(
        description='CloudFormation template builder.'
    )

    REGION_NAME = 'us-east-2'

    # Define command line interface
    my_parser.add_argument('-p', '--path', action='store', type=str,
                           required=True, help="path to AWS credentials file")

    args = my_parser.parse_args()

    PATH = args.path
    STACK_NAME = 'CSE4940'
    API_NAME = 'API'
    API_DEPLOYMENT_NAME = 'ApiInitialDeployment'
    API_STAGE_NAME = 'development'
    API_USAGE_PLAN_NAME = 'ApiUsagePlan'
    API_KEY_NAME = 'ApiKey'
    API_RESOURCES = ['Projects', 'Stacks', 'Users', 'EC2Resources', 'DynamoDBResources']
    API_RESOURCE_METHODS = {
        'Projects': ['DELETE', 'GET', 'POST', 'PUT'],
        'Stacks': ['POST', 'PUT'],
        'Users': ['GET', 'POST'],
        'EC2Resources': ['GET'],
        'DynamoDBResources': ['GET']
    }
    API_LAMBDAS = {
        'DynamoDBResources': {
            'GET': LambdaParams(
                'DynamoDBResourcesGETLambda',
                '/../lambda/dynamodbResources/get.py',
                ['arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess'],
                proxy=True
            )
        },
        'EC2Resources': {
            'GET': LambdaParams(
                'EC2ResourcesGETLambda',
                '/../lambda/ec2Resources/get.py',
                ['arn:aws:iam::aws:policy/AmazonEC2FullAccess'],
                utils.read_mapping_template("../lambda/ec2Resources/GETMappingTemplate")
            )
        },
        'Projects': {
            'DELETE': LambdaParams(
                'ProjectsDELETELambda',
                '/../lambda/projects/delete.py',
                [
                    'arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess',
                    'arn:aws:iam::aws:policy/AmazonEC2FullAccess',
                    'arn:aws:iam::aws:policy/AWSCloudFormationFullAccess'
                ]
            ),
            'GET': LambdaParams(
                'ProjectsGETLambda',
                '/../lambda/projects/get.py',
                ['arn:aws:iam::aws:policy/AmazonDynamoDBReadOnlyAccess'],
                utils.read_mapping_template("../lambda/projects/GETMappingTemplate")
            ),
            'POST': LambdaParams(
                'ProjectsPOSTLambda',
                '/../lambda/projects/post.py',
                ['arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess'],
                utils.read_mapping_template("../lambda/projects/POSTMappingTemplate")
            ),
            'PUT': LambdaParams(
                'ProjectsPUTLambda',
                '/../lambda/projects/put.py',
                ['arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess'],
                utils.read_mapping_template("../lambda/projects/PUTMappingTemplate")
            )
        },
        'Stacks': {
            'POST': LambdaParams(
                'StacksPOSTLambda',
                '/../lambda/stacks/post.py',
                [
                    'arn:aws:iam::aws:policy/AWSCloudFormationFullAccess',
                    'arn:aws:iam::aws:policy/AmazonEC2FullAccess',
                    'arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess',
                ]
            ),
            'PUT': LambdaParams(
                'StacksPUTLambda',
                '/../lambda/stacks/put.py',
                [
                    'arn:aws:iam::aws:policy/AWSCloudFormationFullAccess',
                    'arn:aws:iam::aws:policy/AmazonEC2FullAccess',
                    'arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess',
                ]
            )
        },
        'Users': {
            'GET': LambdaParams(
                'UsersGETLambda',
                '/../lambda/users/get.py',
                ['arn:aws:iam::aws:policy/AmazonDynamoDBReadOnlyAccess']
            ),
            'POST': LambdaParams(
                'UsersPOSTLambda',
                '/../lambda/users/post.py',
                ['arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess'],
                utils.read_mapping_template("../lambda/users/postMappingTemplate")
            )
        }
    }

    ACCESS, SECRET = utils.read_credentials(PATH)
    session = boto3.Session(ACCESS, SECRET, region_name=REGION_NAME)
    template = Template(name=STACK_NAME)

    # Generate Database tables
    template.add_dynamodb_table(
        name='Projects',
        reads=1,
        writes=1
    )
    template.add_dynamodb_table(
        name='Users',
        reads=1,
        writes=1
    )

    # Generate the API Gateway REST API
    template.add_apigateway_api(
        name=API_NAME
    )
    for resource in API_RESOURCES:
        prefixed_methods = [resource+m for m in API_RESOURCE_METHODS[resource]]

        template.add_apigateway_resource(
            name=resource,
            api_name=API_NAME
        )

        for method in API_RESOURCE_METHODS[resource]:
            function = API_LAMBDAS[resource][method]

            template.add_lambda_function(
                name=function.name,
                filename=str(THIS_DIR)+function.file,
                rolename=function.role,
                managed_policies=function.policies
            )

            if function.is_proxy:
                template.add_apigateway_proxy_method(
                    lambda_name=function.name,
                    method_type=method,
                    api_name=API_NAME,
                    resource_name=resource,
                    full_path=resource,
                    require_key=True
                )
            else:
                template.add_apigateway_method(
                    lambda_name=function.name,
                    method_type=method,
                    api_name=API_NAME,
                    resource_name=resource,
                    full_path=resource,
                    require_key=True,
                    mapping_template=function.mapping_template
                )

        template.enable_apigateway_resource_cors(
            resource_name=resource,
            api_name=API_NAME,
            methods=prefixed_methods,
            allow_http_methods=API_RESOURCE_METHODS[resource]
        )

    all_methods = list(
        itertools.chain.from_iterable([
            [k+s for s in API_RESOURCE_METHODS[k]]
            for k in API_RESOURCE_METHODS.keys()
        ])
    )
    template.add_apigateway_deployment(
        name=API_DEPLOYMENT_NAME,
        api_name=API_NAME,
        stage_name=API_STAGE_NAME,
        methods=all_methods
    )
    template.add_apigateway_usage_plan(
        name=API_USAGE_PLAN_NAME,
        api_name=API_NAME,
        key_name=API_KEY_NAME,
        stage_name=API_STAGE_NAME,
        deployment_name=API_DEPLOYMENT_NAME
    )

    # Save a copy of the template
    template.save_as_json(STACK_NAME.lower()+'.json')

    # Submit the template to Cloud Formation for stack construction
    if client.stack_exists(session, STACK_NAME):
        print('Stack "{}" already exists!'.format(STACK_NAME))
        try:
            response = client.update_stack(
                session,
                STACK_NAME,
                template
            )
            print(utils.prettify_json(response))
        except:
            pass
    else:
        response = client.create_stack(
            session=session,
            stack_name=STACK_NAME,
            template=template
        )

        print('Template for stack "{}" uploaded.'.format(STACK_NAME))
        print('Creating... ', end='', flush=True)
        result = client.wait_for_completion(
            session=session,
            stack_name=STACK_NAME,
            api_name=API_NAME,
            key_name=API_KEY_NAME,
            region_name=REGION_NAME,
            stage_name=API_STAGE_NAME
        )

        if result['status']:
            print('SUCCESS')

            del result['status']
            result['stackName'] = STACK_NAME
            with open('confidential.json', 'w') as f:
                f.write(utils.prettify_json(result))
        else:
            print('FAILED')
