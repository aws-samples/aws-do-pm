import copy
import json
import operator
from decimal import Decimal
from functools import reduce  # forward compatibility for Python 3

import boto3
import numpy as np
from pyDOE import lhs


def getFromDict(dataDict, mapList):
    return reduce(operator.getitem, mapList, dataDict)


def setInDict(dataDict, mapList, value):
    getFromDict(dataDict, mapList[:-1])[mapList[-1]] = value


# Upload workload_dict into the workload table
def upload_info_dict_to_dynamodbtable(name, run_specifier, run_id, info_dict, dynamodb=None, region_name='us-east-1'):
    if dynamodb is None:
        dynamodb = boto3.resource('dynamodb', region_name=region_name)

    table = dynamodb.Table(name)
    add_dict = {
        'run_specifier': run_specifier,
        'run_index': int(run_id),
        'info': info_dict
    }
    add_dict_d = json.loads(json.dumps(add_dict), parse_float=Decimal)
    table.put_item(Item=add_dict_d)


# Upload workload_dict into the workload table
def batch_upload_info_dict_to_dynamodbtable(name, run_specifier, run_id_list, info_dict_list, dynamodb=None,
                                            region_name='us-east-1'):
    if dynamodb is None:
        dynamodb = boto3.resource('dynamodb', region_name=region_name)

    table = dynamodb.Table(name)
    n_records = len(run_id_list)
    print('Starting Batch Insert')
    with table.batch_writer() as batch:
        for run_id, info_dict in zip(run_id_list, info_dict_list):
            add_dict = {
                'run_specifier': run_specifier,
                'run_index': int(run_id),
                'info': info_dict
            }
            # Dynamodb does not accept Float, convert to Decimal
            add_dict_d = json.loads(json.dumps(add_dict), parse_float=Decimal)
            # https://pypi.org/project/dynamodb-json/
            # add_dict_d = json_util.dumps(json.dumps(add_dict))
            batch.put_item(Item=add_dict_d)
    print('Completed Batch Insert: %d Records' % (n_records))


def generate_json_dict_array(n_runs, workload_config, bounds_config):
    ret_list = []
    # Determine the Hierarchical parameter to change
    n_vars = len(bounds_config)
    lhd = lhs(n_vars, samples=n_runs)

    # Convert from coded to actual space and apply the type casting

    tree_path_list = []
    uncoded_val_list = []
    for i_var in np.arange(n_vars):
        cur_coded_1d = lhd[:, i_var]
        tree_path = bounds_config[i_var]['tree_path']
        type_bounds_dict = bounds_config[i_var]['type_bounds']
        lb = type_bounds_dict['lb']
        ub = type_bounds_dict['ub']
        var_type = type_bounds_dict['type']
        cur_uncoded_1d = lb + cur_coded_1d * (ub - lb)
        if var_type == "int":
            cur_uncoded_1d = (np.round(cur_uncoded_1d)).astype(np.int)
        uncoded_val_list.append(cur_uncoded_1d)
        tree_path_list.append(tree_path)

    # Loop through the runs and generate the input jsons
    for i_run in np.arange(n_runs):
        cur_workload_copy = copy.deepcopy(workload_config)
        for i_var in np.arange(n_vars):
            setInDict(cur_workload_copy, tree_path_list[i_var], (uncoded_val_list[i_var][i_run]).item())

        # Dump this json to s3
        # key_jsonfile = 'input/input%d.json'%(i_run)
        # serialized_json = json.dumps(cur_workload_copy)
        ret_list.append(cur_workload_copy)
        # s3client.put_object(Bucket=bucket_name, Key='%s/%s'%(scenario_name, key_jsonfile), Body=serialized_json)

    return ret_list


def extract_lb_ub(bounds_config):
    n_vars = len(bounds_config)
    lb_list = []
    ub_list = []
    for cur_bc in bounds_config:
        lb_list.append(cur_bc['type_bounds']['lb'])
        ub_list.append(cur_bc['type_bounds']['ub'])
    return lb_list, ub_list


def generate_candidate_workload_dict(val_list, workload_config, bounds_config):
    ret_dict = copy.deepcopy(workload_config)
    n_vars = len(bounds_config)
    # Strip the val list, to use only the main values.. no need to save the gene
    val_list = val_list[:n_vars]
    for i_var in np.arange(n_vars):
        tree_path = bounds_config[i_var]['tree_path']
        type_bounds_dict = bounds_config[i_var]['type_bounds']
        var_type = type_bounds_dict['type']
        if var_type == "int":
            rounded_val = (np.round(val_list[i_var])).item()  # astype(np.int)
            setInDict(ret_dict, tree_path, rounded_val)
        else:
            setInDict(ret_dict, tree_path, val_list[i_var])

    return ret_dict


def generate_lhs_sampling(n_samples, bounds_config):
    # Do the sampling in coded space and then convert it back to uncoded space
    # Determine the Hierarchical parameter to change
    n_vars = len(bounds_config)
    lhd = lhs(n_vars, samples=n_samples)

    # Convert from coded to actual space and apply the type casting
    uncoded_val_list = []
    for i_var in np.arange(n_vars):
        cur_coded_1d = lhd[:, i_var]
        type_bounds_dict = bounds_config[i_var]['type_bounds']
        var_type = type_bounds_dict['type']
        lb = type_bounds_dict['lb']
        ub = type_bounds_dict['ub']
        cur_uncoded_1d = lb + cur_coded_1d * (ub - lb)
        if var_type == "int":
            cur_uncoded_1d = (np.round(cur_uncoded_1d)).astype(np.int)
        uncoded_val_list.append(cur_uncoded_1d)
    return np.array(uncoded_val_list).T
