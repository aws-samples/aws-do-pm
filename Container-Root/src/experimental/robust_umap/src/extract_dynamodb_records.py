import json
import boto3
import numpy as np
from decimal import Decimal
import random
import copy
from dynamodb_json import json_util
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key


# query_table(table_name, key='run_specifier', value=run_specifier_str, ...)
# eval_dict_converted = [json_util.loads(cur_item['info']) for cur_item in resp_dict['Items']]
def query_dynamodb_record(name, key, value, region_name, dynamodb=None):
    if dynamodb is None:
        dynamodb = boto3.resource('dynamodb', region_name=region_name)

    ret_dict = {}
    table = dynamodb.Table(name)

    if key is not None and value is not None:
        filtering_exp = Key(key).eq(value)
        response = table.query(KeyConditionExpression=filtering_exp)
        if(response['Count'] > 0):
            ret_dict = [json_util.loads(cur_item['info']) for cur_item in response['Items']]

    return ret_dict

    raise ValueError('Parameters missing or invalid')


# Extract records as a dict and return
# If run_id is None, it will return all records for that run_specifier
def extract_dynamodb_record(name, run_specifier, region_name, run_id=None, dynamodb=None):
    if dynamodb is None:
        dynamodb = boto3.resource('dynamodb', region_name=region_name)

    table = dynamodb.Table(name)

    try:
        if run_id is not None:
            response = table.get_item(Key={'run_specifier': run_specifier, 'run_index': run_id})
        else:
            response = table.get_item(Key={'run_specifier': run_specifier})

    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        return response['Item']


if __name__ == "__main__":
    # from table_definition import table_name, ga_detail_table_name, ga_overview_table_name, region_name
    import configparser

    config = configparser.RawConfigParser()
    config.read('config.properties')

    region_name = config.get('COMMON', 'region_name')
    table_name = config.get('GA', 'table_name')
    ga_overview_table_name = config.get('GA', 'ga_overview_table_name')
    ga_detail_table_name = config.get('GA', 'ga_detail_table_name')

    dynamodb = boto3.resource('dynamodb', region_name=region_name)

    # Extract from ga_overview_table_name
    # All records under hash
    resp_dict = query_dynamodb_record(name=ga_overview_table_name,
                                      key='run_specifier',
                                      value='ga_scenario1',
                                      region_name=region_name,
                                      dynamodb=dynamodb)

    # Record for hash & range key
    resp_dict = extract_dynamodb_record(ga_overview_table_name,
                                        run_specifier='ga_scenario1',
                                        region_name=region_name,
                                        run_id=0,
                                        dynamodb=dynamodb)
    parent_offspring_hash = resp_dict['info']['population']
    # Extract from ga_detail_table_name
    hash_str = parent_offspring_hash
    # All records under hash
    resp_dict = query_dynamodb_record(name=ga_detail_table_name,
                                      key='run_specifier',
                                      value=hash_str,
                                      region_name=region_name,
                                      dynamodb=dynamodb)

    # Record for hash & range key
    resp_dict = extract_dynamodb_record(ga_detail_table_name,
                                        run_specifier=hash_str,
                                        region_name=region_name,
                                        run_id=0,
                                        dynamodb=dynamodb)

    # All records under hash
    resp_dict = query_dynamodb_record(name=table_name,
                                      key='run_specifier',
                                      value=hash_str,
                                      region_name=region_name,
                                      dynamodb=dynamodb)

    # Record for hash & range key
    resp_dict = extract_dynamodb_record(table_name,
                                        run_specifier=hash_str,
                                        region_name=region_name,
                                        run_id=0,
                                        dynamodb=dynamodb)
