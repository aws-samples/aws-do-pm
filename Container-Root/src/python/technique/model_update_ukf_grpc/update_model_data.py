######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

import copy
import os
import json
import sys
import grpc
from datetime import datetime
import argparse
import numpy as np
from run_ukf import run_ukf
from lib.util.dict_util import dict_merge
import time

sys.path.append("/app/grpc_compiled")

from grpc_compiled import model_interface_pb2, model_interface_pb2_grpc
from lib.grpc.retry_interceptor import RetryOnRpcErrorClientInterceptor, ExponentialBackoff


# def run_task(predict_json, num_output_points, num_ukf_iter, **kwargs):
def run_task(task_dict, service_dict): #predict_json, num_output_points, num_ukf_iter, **kwargs):
    task_analyticSettings = task_dict['analyticSettings']
    num_output_points = task_analyticSettings['num_output_points']
    num_ukf_iter = task_analyticSettings['num_ukf_iter']
    model_dict = task_analyticSettings['model']

    # Find Length of the stacked input of all the list
    tunableParams = model_dict['analyticSettings']['tunableParams']
    n_inp_vars = 0
    for key, value in tunableParams.items():
        n_inp_vars += len(value)

    # Augment the ukf parameters
    # Pick the val numbers based on the first element and apply it on all the input variables
    P_val = task_analyticSettings['ukf']['P'][0]
    Q_val = task_analyticSettings['ukf']['Q'][0]
    task_analyticSettings['ukf']['P'] = n_inp_vars * [P_val]
    task_analyticSettings['ukf']['Q'] = n_inp_vars * [Q_val]
    task_analyticSettings['ukf']['max_iter'] = [num_ukf_iter]

    calib_model_dict = copy.deepcopy(model_dict)
    calib_model_dict['description'] = 'Model Updated w/ UKF'
    calib_model_dict['filename'] = 'model.json'

    # Pass through the inputs and outputs from the task_dict
    calib_model_dict['inputs'] = task_dict['inputs']
    calib_model_dict['outputs']['actual'] = task_dict['outputs']['actual']

    name_port = '%s:%s'%(service_dict['metadata']['name'], service_dict['metadata']['port_internal'])
    interceptors = (
        RetryOnRpcErrorClientInterceptor(
            max_attempts=5,
            sleeping_policy=ExponentialBackoff(init_backoff_ms=1000, max_backoff_ms=30000, multiplier=2),
            status_for_retry=(grpc.StatusCode.UNAVAILABLE,),
        ),
    )
    stub = model_interface_pb2_grpc.ModelServiceStub(
        grpc.intercept_channel(grpc.insecure_channel(name_port), *interceptors)
    )

    input_var_order = calib_model_dict['analyticSettings']['modelParams']['input_var_order']
    # Find the number of rows from either the inputs or outputs
    n_rows = len(calib_model_dict['inputs'][input_var_order[0]])
    if (num_output_points < n_rows):
        idx = np.round(np.linspace(0, n_rows - 1, num_output_points)).astype(int)
    else:
        idx = np.arange(n_rows)

    for idx_var, cur_var in enumerate(input_var_order):
        calib_model_dict['inputs'][cur_var] = np.array(calib_model_dict['inputs'][cur_var])[idx].squeeze().tolist()
    # Set the actual outputs just in case we want to use this object for ukf
    # y's are single column
    output_var_order = calib_model_dict['analyticSettings']['modelParams']['output_var_order']
    for idx_var, cur_var in enumerate(output_var_order):
        calib_model_dict['outputs']['actual'][cur_var] = np.array(calib_model_dict['outputs']['actual'][cur_var])[idx].squeeze().tolist()

    # Set the task dict with the calib_model_dict
    task_dict['analyticSettings']['model'] = calib_model_dict

    tunable_params, tunable_params_cov = run_ukf(grpc_stub=stub, ukf_input_dict=task_dict)

    calib_model_dict['analyticSettings']['tunableParams'] = tunable_params
    calib_model_dict['analyticSettings']['tunableParamsCov'] = tunable_params_cov

    # Output the dictionary at the target location
    pm_root_path=os.getenv('PM_ROOT_PATH',default='wd')
    rel_dest_path = task_analyticSettings['rel_dest_path']
    dest_path_full = '%s/%s'%(pm_root_path,rel_dest_path)
    os.makedirs(dest_path_full, exist_ok=True)
    task_model_details_filepath_full = '%s/model.json' % (dest_path_full)
    with open(task_model_details_filepath_full, 'w') as fp:
        json.dump(calib_model_dict, fp)
        print('Exported: %s' % (task_model_details_filepath_full))

    meta_data_filepath_full = '%s/metadata.json'%(dest_path_full)
    meta_data_dict = {
        'metadata': calib_model_dict
    }
    with open(meta_data_filepath_full, 'w') as fp:
        json.dump(meta_data_dict, fp)
        print('Exported: %s' % (meta_data_filepath_full))


def export_status(task_json_path_full):
    # Export the status file
    timestr = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    status_path_full = '%s_status.json'%(os.path.splitext(task_json_path_full)[0])
    with open(status_path_full, 'w') as fp:
        status_dict = {
            'timestamp': timestr,
            'return_status': 0
        }
        json.dump(status_dict, fp)
        print('Export task status: %s' % (status_path_full))

if __name__ == "__main__":

    time.sleep(12) # Allow container to start up
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', help='Relative path to the json file describing this model build task')
    args = parser.parse_args()

    task_json_path_full = '%s' % (args.config)
    with open(task_json_path_full, 'r') as fp:
        task_dict = json.load(fp)

    # Extract the data and model locations
    # Update it back in the task dict
    # TODO: A cleaner segregation is needed here
    pm_root_path=os.getenv('PM_ROOT_PATH',default='wd')
    rel_data_path = task_dict['analyticSettings']['rel_data_path']

    rel_service_path = task_dict['analyticSettings']['rel_service_path']
    data_metadata_json = '%s/%s/metadata.json'%(pm_root_path,rel_data_path)
    with open(data_metadata_json, 'r') as fp:
        data_metadata_dict = json.load(fp)

    data_filename = data_metadata_dict['metadata']['filename']
    with open('%s/%s/%s'%(pm_root_path,rel_data_path, data_filename), 'r') as fp:
        data_dict = json.load(fp)

    with open('%s/%s/metadata.json'%(pm_root_path,rel_service_path), 'r') as fp:
        service_dict = json.load(fp)

    dict_merge(task_dict, data_dict)
    # Get the model dict from the service metadata instead of a model node
    task_dict['analyticSettings']['model'] = service_dict['metadata']['model']

    run_task(task_dict,service_dict)

    # Export the status
    export_status(task_json_path_full=task_json_path_full)
