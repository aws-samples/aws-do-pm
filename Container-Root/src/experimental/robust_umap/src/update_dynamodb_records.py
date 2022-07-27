import json
import boto3
import numpy as np
from decimal import Decimal
import random
import copy
from botocore.exceptions import ClientError


def update_dynamodb_info(name, hash_str, id, update_expression, expression_attribute_values, dynamodb=None, region_name='us-east-1'):
    if dynamodb is None:
        dynamodb = boto3.resource('dynamodb', region_name=region_name)

    table = dynamodb.Table(name)
    try:
        response = table.update_item(
            Key={'run_specifier': hash_str, 'run_index': id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues='UPDATED_NEW'
        )
        return response
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        return response['Item']

