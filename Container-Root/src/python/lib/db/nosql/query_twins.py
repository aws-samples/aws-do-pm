######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

import json
import argparse
from dynamodb_access import DynamoDBAccess

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--asset_id', help='Asset ID')

    args = parser.parse_args()
    loc_dynamodb_access = DynamoDBAccess()

    criterion_dict = {
        'asset_id': args.asset_id
    }

    print('Search Criterion')
    print(json.dumps(criterion_dict))
    print('Model Table Query Results')
    ret_list = loc_dynamodb_access.query_dynamodb_record_model(key_criterion=criterion_dict)
    print(ret_list)

    print('History Table Query Results')
    ret_list = loc_dynamodb_access.query_dynamodb_record_history(key_criterion=criterion_dict)
    print(ret_list)

    # encoded_config_json = os.getenv('ENCODED_CONFIG_JSON')
    # config_dict = base64_decode_json(encoded_config_json)
    #
    # region_name = config_dict['common']['region_name']
    # model_table = config_dict['dynamodb']['model_table']
    #
    # # Insert this record into the dynamodb
    # criterion_dict = {
    #     'asset_id': args.asset_id
    # }
    # ret_list = query_dynamodb_record(table_name=model_table,
    #                                  key_criterion=criterion_dict,
    #                                  region_name=region_name)
    # print(ret_list)
