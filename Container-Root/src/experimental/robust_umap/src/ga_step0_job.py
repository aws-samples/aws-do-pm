import json

import boto3
import numpy as np

from create_dynamodb_tables import check_create_dynamodb_table
from insert_dynamodb_records import generate_lhs_sampling, generate_candidate_workload_dict
from insert_dynamodb_records import upload_info_dict_to_dynamodbtable, batch_upload_info_dict_to_dynamodbtable
from utils.hash_utils import generate_hash_str

if __name__ == "__main__":
    from table_definition import table_key_schema, table_attribute_def

    import configparser

    config = configparser.RawConfigParser()
    config.read('./template/config_template.conf')
    common_dict = config._sections['common']
    ga_dict = config._sections['GA']

    region_name = common_dict['region_name']
    table_name = ga_dict['table_name']
    ga_overview_table_name = ga_dict['ga_overview_table_name']
    ga_detail_table_name = ga_dict['ga_detail_table_name']
    n_char = int(ga_dict['n_char'])
    ga_scenario_specifier = ga_dict['scenario_specifier']
    n_population = int(ga_dict['n_population'])

    with open('./template/workload_config_template.json', 'r') as fp:
        workload_config = json.load(fp)

    with open('./template/lhs_bounds_template.json', 'r') as fp:
        bounds_config = json.load(fp)

    session = boto3.session.Session()
    dynamodb = session.resource('dynamodb', region_name=region_name)

    # Create the workload table
    check_create_dynamodb_table(
        name=table_name,
        key_schema=table_key_schema,
        attribute_def=table_attribute_def,
        region_name=region_name,
        dynamodb=dynamodb
    )

    # Create the workload ga table
    check_create_dynamodb_table(
        name=ga_overview_table_name,
        key_schema=table_key_schema,
        attribute_def=table_attribute_def,
        region_name=region_name,
        dynamodb=dynamodb
    )

    check_create_dynamodb_table(
        name=ga_detail_table_name,
        key_schema=table_key_schema,
        attribute_def=table_attribute_def,
        region_name=region_name,
        dynamodb=dynamodb
    )

    # %%
    # Create a new Hash string
    cur_generation = 0
    run_specifier_str = generate_hash_str(n_char=n_char)
    # Insert a new record into the as parent
    info_dict = {
        'population': run_specifier_str
    }
    upload_info_dict_to_dynamodbtable(name=ga_overview_table_name,
                                      run_specifier=ga_scenario_specifier,
                                      run_id=cur_generation,
                                      info_dict=info_dict,
                                      dynamodb=dynamodb,
                                      region_name=region_name)

    # %%
    # Enter records into Workload and Detail Table
    lhs_sample_2d = generate_lhs_sampling(n_samples=n_population,
                                          bounds_config=bounds_config)

    # %%
    # create workload & ga detail dictionaries for batch insert &
    n_rows, n_cols = lhs_sample_2d.shape
    wl_dict_list = []
    ga_detail_dict_list = []
    for i_row in np.arange(n_rows):
        cur_val_list = list(lhs_sample_2d[i_row, :])
        loc_wl_dict = generate_candidate_workload_dict(cur_val_list, workload_config, bounds_config)
        loc_ga_detail_dict = {
            'candidate': cur_val_list
        }
        wl_dict_list.append(loc_wl_dict)
        ga_detail_dict_list.append(loc_ga_detail_dict)

    # Batch upload the dict to a dynamo table
    batch_upload_info_dict_to_dynamodbtable(name=ga_detail_table_name,
                                            run_specifier=run_specifier_str,
                                            run_id_list=list(np.arange(n_rows)),
                                            info_dict_list=ga_detail_dict_list,
                                            dynamodb=dynamodb,
                                            region_name=region_name)
    batch_upload_info_dict_to_dynamodbtable(name=table_name,
                                            run_specifier=run_specifier_str,
                                            run_id_list=list(np.arange(n_rows)),
                                            info_dict_list=wl_dict_list,
                                            dynamodb=dynamodb,
                                            region_name=region_name)
