######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

import copy
import os
import json
import sys
import grpc
import argparse
import numpy as np
import pandas as pd
from lib.util.dict_util import dict_merge, flatten_dol, unflatten_dol
import matplotlib.pyplot as plt
import time

sys.path.append("/app/grpc_compiled")

from grpc_compiled import model_interface_pb2, model_interface_pb2_grpc
from lib.util.encode_decode_json import utf_encode_json, utf_decode_json
from lib.grpc.retry_interceptor import RetryOnRpcErrorClientInterceptor, ExponentialBackoff

def _run_prediction(stub, model_dict):
    model_dict_enc = utf_encode_json(model_dict)
    query = model_interface_pb2.inRequest(inp_dict_bytes=model_dict_enc)
    response = stub.EvaluateModel(query)
    response_dict = utf_decode_json(response.response_bytes)

    return response_dict

def run_task(task_dict, hostname, port, **kwargs):
    # Location has to flow in formally
    name_port = '%s:%s'%(hostname, port)

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

    # Get the analyticSettings of the model
    task_analyticSettings = task_dict['analyticSettings']
    model_dict = task_analyticSettings['model']
    model_analyticSettings = model_dict['analyticSettings']
    tunableParams = model_analyticSettings['tunableParams']

    num_samples = task_analyticSettings['num_samples']

    # Save the map
    _tunableParams_flat, _, _tunableParams_map = flatten_dol(tunableParams)

    isTunableParamsCov = 'tunableParamsCov' in model_analyticSettings

    predict_model_dict = copy.deepcopy(model_dict)
    # Add the inputs and outputs to it
    predict_model_dict['inputs'] = task_dict['inputs']
    predict_model_dict['outputs'] = task_dict['outputs']

    # Run the base prediction with this dictionary
    model_output = _run_prediction(stub=stub, model_dict=predict_model_dict)
    nominal_pred_pd = pd.DataFrame.from_dict(model_output['prediction'])
    output_names = nominal_pred_pd.columns
    ret_dict = {}
    ret_dict['description']: 'Model Prediction w/ GRPC'
    ret_dict['filename'] = 'metadata.json'
    for cur_name in output_names:
        ret_dict[cur_name] = {
            'nominal': nominal_pred_pd[cur_name].values.tolist()
        }
    # Output the dictionary at the target location
    rel_dest_path = task_analyticSettings['rel_dest_path']
    file_list = []
    pm_root_path = os.getenv('PM_ROOT_PATH',default='wd')
    dest_path_full = '%s/%s'%(pm_root_path,rel_dest_path)
    os.makedirs(dest_path_full, exist_ok=True)
    nominal_pred_out_fname = '%s/nominal_pred.csv'%(dest_path_full)
    nominal_pred_pd.to_csv(nominal_pred_out_fname)
    file_list.append(nominal_pred_out_fname)

    # If the output has both actual and predicted, calculate the MAE error
    try:
        actual_output_dict = task_dict['outputs']['actual']
        prediction_output_dict = model_output['prediction']
        # ret_output = ret_model_json_predict['outputs']
        output_dict_keys = list(actual_output_dict.keys())
        predict_details_dict = {}
        output_mae = {}
        # Calculate the Error
        var_names = list(actual_output_dict.keys())
        for cur_var_name in var_names:
            loc_actual = np.array(actual_output_dict[cur_var_name])
            loc_prediction = np.array(prediction_output_dict[cur_var_name])
            output_mae[cur_var_name] = np.mean(np.abs(loc_actual - loc_prediction))
        predict_details_dict['mae'] = output_mae
        mae_list = []
        for k, v in output_mae.items():
            mae_list.append(v)

        predict_details_dict['mae_overall'] = np.mean(np.array(mae_list))
    except:
        pass


    if (isTunableParamsCov):
        tunableParamsCov = model_analyticSettings['tunableParamsCov']['P']
        # Prepare the list of samples to run the model for
        current_state = np.array(_tunableParams_flat)
        current_cov = np.array(tunableParamsCov)
        # generate samples
        samples_2d = np.random.multivariate_normal(current_state, current_cov, num_samples)
        pred_unc_pd_list = list()
        for idx_sample in np.arange(num_samples):
            this_sample = samples_2d[idx_sample, :]
            predict_model_dict['analyticSettings']['tunableParams'] = unflatten_dol(this_sample.tolist(), _tunableParams_map)
            this_sample_output = _run_prediction(stub=stub, model_dict=predict_model_dict)
            loc_pd = pd.DataFrame.from_dict(this_sample_output['prediction'])
            loc_pd['sample_idx'] = idx_sample
            pred_unc_pd_list.append(loc_pd)

        pred_unc_pd = pd.concat(pred_unc_pd_list).reset_index()

        for cur_name in output_names:
            pred_unc_pd_pivot = pred_unc_pd.pivot_table(index='index', columns='sample_idx', values=cur_name)
            y_min = np.min(pred_unc_pd_pivot, axis=1)
            y_max = np.max(pred_unc_pd_pivot, axis=1)

            ret_dict[cur_name]['min'] = y_min.tolist()
            ret_dict[cur_name]['max'] = y_max.tolist()

        uncertainty_pred_out_fname = '%s/uncertainty_pred.csv'%(dest_path_full)
        pred_unc_pd.to_csv(uncertainty_pred_out_fname)
        file_list.append(uncertainty_pred_out_fname)

    # Generate the y_min and y_max plot
    fig, ax = plt.subplots(len(output_names), 1, sharex=True)
    for idx_ax, cur_name in enumerate(output_names):
        if(len(output_names) > 1):
            cur_ax = ax[idx_ax]
        else:
            cur_ax = ax

        cur_dict = ret_dict[cur_name]
        if(('min' in cur_dict) & ('max' in cur_dict)):
            cur_ax.fill_between(np.arange(len(cur_dict['nominal'])), cur_dict['min'], cur_dict['max'], facecolor='orange', alpha=0.4)
        if('nominal' in cur_dict):
            cur_ax.plot(np.arange(len(cur_dict['nominal'])), cur_dict['nominal'])
        cur_ax.set_ylabel(cur_name)
        cur_ax.grid()

    fig.savefig('%s/prediction.png'%(dest_path_full))
    plt.close(fig)

    meta_data_filepath_full = '%s/metadata.json'%(dest_path_full)
    meta_data_dict = {
        'metadata': {**ret_dict, **predict_details_dict},
        'file_list': file_list
    }
    with open(meta_data_filepath_full, 'w') as fp:
        json.dump(meta_data_dict, fp)
        fp.flush()
        os.fsync(fp.fileno())
        print('Exported: %s' % (meta_data_filepath_full))
    fp.close()
    
    fd = os.open(dest_path_full,os.O_RDONLY)
    os.fsync(fd)
    os.close(fd)

if __name__ == "__main__":
    time.sleep(12) # allow container startup time
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

    run_task(task_dict,service_dict['metadata']['name'], service_dict['metadata']['port_internal'])
