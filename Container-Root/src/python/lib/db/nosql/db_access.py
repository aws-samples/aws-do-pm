######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

import boto3
import json
from dynamodb_json import json_util
from boto3.dynamodb.conditions import Key, And
from decimal import Decimal
from botocore.exceptions import ClientError
from functools import reduce

from itertools import islice
from datetime import datetime

def create_chunks(list_name, n):
    for i in range(0, len(list_name), n):
        yield list_name[i:i + n]


# Upload workload_dict into the workload table
def upload_dbitem_to_dynamodbtable(table_name, model_id, asset_id, model_type, update_seq, tunable_params, region_name, dynamodb=None, **kwargs):
    print('Starting, Single Insert: %s, %s, %s, %d' % (table_name, model_id, asset_id, update_seq))
    if dynamodb is None:
        dynamodb = boto3.resource('dynamodb', region_name=region_name, endpoint_url='http://localstack:4566')

    table = dynamodb.Table(table_name)
    # info_dict = ins_dbitem  # .export_dict()
    add_dict = {
        'model_id': model_id,
        'asset_id': asset_id,
        'model_type': model_type,
        'update_seq': update_seq,
        'tunable_params': tunable_params
    }
    add_dict_d = json.loads(json.dumps(add_dict), parse_float=Decimal)
    table.put_item(Item=add_dict_d)


# Very expensive operation, use with care
# https://stackoverflow.com/questions/10450962/how-can-i-fetch-all-items-from-a-dynamodb-table-without-specifying-the-primary-k
def scan_dynamodb(table_name, region_name, dynamodb=None):
    if dynamodb is None:
        dynamodb = boto3.resource('dynamodb', region_name=region_name, endpoint_url='http://localstack:4566')
    table = dynamodb.Table(table_name)
    response = table.scan()
    ret_list = response['Items']
    return ret_list

# https://stackoverflow.com/questions/63679436/dynamodb-and-boto3-chain-multiple-conditions-in-scan
def query_dynamodb_record(table_name, key_criterion, region_name, dynamodb=None):
    if dynamodb is None:
        dynamodb = boto3.resource('dynamodb', region_name=region_name, endpoint_url='http://localstack:4566')

    ret_list = []
    table = dynamodb.Table(table_name)

    filtering_exp = reduce(And, ([Key(k).eq(v) for k, v in key_criterion.items()]))
    response = table.query(KeyConditionExpression=filtering_exp)
    if (response['Count'] > 0):
        # ret_list = [json_util.loads(cur_item['info']) for cur_item in response['Items']]
        ret_list = [json_util.loads(cur_item) for cur_item in response['Items']]
    return ret_list

#
# # Extract records as a dict and return
# # If cycle_index is None, it will return all records for that twin_id
# def extract_dynamodb_record(name, twin_id, cycle_index, region_name, dynamodb=None):
#     if dynamodb is None:
#         dynamodb = boto3.resource('dynamodb', region_name=region_name, endpoint_url='http://localstack:4566')
#
#     table = dynamodb.Table(name)
#
#     try:
#         response = table.get_item(Key={'twin_id': twin_id, 'cycle_index': cycle_index})
#
#     except ClientError as e:
#         print(e.response['Error']['Message'])
#     else:
#         ret_dbi = json_util.loads(response['Item']['info'])
#         return ret_dbi
