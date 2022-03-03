######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

import os
import boto3
import json
from dynamodb_json import json_util
from db_access_interface import DBAccessInterface
from boto3.dynamodb.conditions import Key, And
from decimal import Decimal
from functools import reduce

class DynamoDBAccess(DBAccessInterface):
    def __init__(self):
        self.region_name = os.getenv('AWS_DEFAULT_REGION') #region_name
        self.endpoint_url = os.getenv('AWS_ENDPOINT') # endpoint_url
        self.pm_db_table_model = os.getenv('PM_DB_TABLE_MODEL')
        self.pm_db_table_history = os.getenv('PM_DB_TABLE_HISTORY')
        print('Creating DynamoDB Resource: %s, %s'%(self.endpoint_url, self.region_name))
        if self.endpoint_url:
            self.dynamodb_resource = boto3.resource('dynamodb', region_name=self.region_name, endpoint_url=self.endpoint_url)
        else:
            self.dynamodb_resource = boto3.resource('dynamodb', region_name=self.region_name)
        self.dynamodb_client = self.dynamodb_resource.meta.client

    def _atomic_create_db_table(self, name, key_schema, attribute_def):
        waiter = self.dynamodb_client.get_waiter('table_exists')

        # Check if table exists
        existing_tables = self.dynamodb_client.list_tables()['TableNames']

        billing_mode = 'PAY_PER_REQUEST'

        if (name not in existing_tables):
            table = self.dynamodb_resource.create_table(
                TableName=name,
                KeySchema=key_schema,
                AttributeDefinitions=attribute_def,
                BillingMode=billing_mode
            )

            # Wait for table creation
            print('Create: Waiting for', name, '...')
            waiter.wait(TableName=name, WaiterConfig={'Delay': 1})

        else:
            print('Table: %s, Exists' % (name))
            print('\tSkipping Creation & Update')

    def check_create_db_table(self):
        # Create the Model Table
        key_schema = [
            {'AttributeName': 'asset_id', 'KeyType': 'HASH'},
            {'AttributeName': 'model_id', 'KeyType': 'RANGE'}
        ]

        attribute_def = [
            {'AttributeName': 'asset_id', 'AttributeType': 'S'},
            {'AttributeName': 'model_id', 'AttributeType': 'S'}
        ]
        self._atomic_create_db_table(name=self.pm_db_table_model,
                                     key_schema=key_schema,
                                     attribute_def=attribute_def)

        # Create the History Table
        # The Table structure is fixed
        key_schema = [
            {'AttributeName': 'asset_id', 'KeyType': 'HASH'},
            {'AttributeName': 'route_id', 'KeyType': 'RANGE'}
        ]

        attribute_def = [
            {'AttributeName': 'asset_id', 'AttributeType': 'S'},
            {'AttributeName': 'route_id', 'AttributeType': 'N'}
        ]
        self._atomic_create_db_table(name=self.pm_db_table_history,
                                     key_schema=key_schema,
                                     attribute_def=attribute_def)

    def _atomic_check_delete_dynamodb_table(self, name):
        print('Deleting DynamoDB Table: %s' % (name))
        return self.dynamodb_client.delete_table(TableName=name)


    def check_delete_db_table(self):
        self._atomic_check_delete_dynamodb_table(self.pm_db_table_model)
        self._atomic_check_delete_dynamodb_table(self.pm_db_table_history)

    def upload_dbitem_db_table(self, table_name, add_dict):
        print('Inserting: %s, %s'%(table_name, json.dumps(add_dict)))
        table = self.dynamodb_resource.Table(table_name)
        # info_dict = ins_dbitem  # .export_dict()
        add_dict_d = json.loads(json.dumps(add_dict), parse_float=Decimal)
        table.put_item(Item=add_dict_d)

    def upload_dbitem_db_modeltable(self, add_dict):
        self.upload_dbitem_db_table(self.pm_db_table_model, add_dict=add_dict)

    def upload_dbitem_db_historytable(self, add_dict):
        self.upload_dbitem_db_table(self.pm_db_table_history, add_dict=add_dict)

    def query_dynamodb_record(self, table_name, key_criterion):
        ret_list = []
        table = self.dynamodb_resource.Table(table_name)

        filtering_exp = reduce(And, ([Key(k).eq(v) for k, v in key_criterion.items()]))
        response = table.query(KeyConditionExpression=filtering_exp)
        if (response['Count'] > 0):
            # ret_list = [json_util.loads(cur_item['info']) for cur_item in response['Items']]
            ret_list = [json_util.loads(cur_item) for cur_item in response['Items']]
        return ret_list

    def query_dynamodb_record_model(self, key_criterion):
        return self.query_dynamodb_record(self.pm_db_table_model, key_criterion=key_criterion)

    def query_dynamodb_record_history(self, key_criterion):
        return self.query_dynamodb_record(self.pm_db_table_history, key_criterion=key_criterion)
