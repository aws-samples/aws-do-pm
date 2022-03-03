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
from tqdm import tqdm
from smt.sampling_methods import LHS
from lib.util.dict_util import dict_merge, flatten_dol, unflatten_dol
from sobol_sensitivity import SobolSensitivity

sys.path.append("/app/grpc_compiled")

from grpc_compiled import model_interface_pb2, model_interface_pb2_grpc
from lib.util.encode_decode_json import utf_encode_json, utf_decode_json

def _run_prediction(stub, model_dict):
    model_dict_enc = utf_encode_json(model_dict)
    query = model_interface_pb2.inRequest(inp_dict_bytes=model_dict_enc)
    response = stub.EvaluateModel(query)
    response_dict = utf_decode_json(response.response_bytes)

    return response_dict

def run_task(task_dict, hostname, port, **kwargs):

    # import debugpy; debugpy.listen(('0.0.0.0',5677)); debugpy.wait_for_client(); breakpoint()

    # Location has to flow in formally
    name_port = '%s:%s'%(hostname, port)
    channel = grpc.insecure_channel(name_port)
    stub = model_interface_pb2_grpc.ModelServiceStub(channel)

    # Get the analyticSettings of the model
    task_analyticSettings = task_dict['analyticSettings']
    model_dict = task_analyticSettings['model']
    model_analyticSettings = model_dict['analyticSettings']
    tunableParams = model_analyticSettings['tunableParams']

    num_samples = task_analyticSettings['num_samples']
    num_background_samples = task_analyticSettings['num_background_samples']

    # Output the dictionary at the target location
    rel_dest_path = task_analyticSettings['rel_dest_path']
    file_list = []
    os.makedirs(rel_dest_path, exist_ok=True)
    pm_root_path=os.getenv('PM_ROOT_PATH',default='wd')
    dest_path_full = '%s/%s'%(pm_root_path,rel_dest_path)

    # Pick the representative input that can be passed into the prediction request
    subselect_inputs = {}
    inputs_min_dict = {}
    inputs_max_dict = {}
    inputs_name_list = list(task_dict['inputs'].keys())
    for k, v in task_dict['inputs'].items():
        subselect_inputs[k] = [task_dict['inputs'][k][0]]
        inputs_min_dict[k] = np.min(task_dict['inputs'][k])
        inputs_max_dict[k] = np.max(task_dict['inputs'][k])

    # Save the map
    percent_range = task_analyticSettings['percent_range']
    _tunableParams_flat, _tunableParams_name_flat, _tunableParams_map = flatten_dol(tunableParams)
    _tunableParams_flat_min = [x * (1.0 - percent_range/100.) for x in _tunableParams_flat]
    _tunableParams_flat_max = [x * (1.0 + percent_range/100.) for x in _tunableParams_flat]
    n_tunableParams = len(_tunableParams_name_flat)
    _inputParams_flat, _inputParams_name_flat, _inputParams_map = flatten_dol(subselect_inputs)
    _inputParams_flat_min = [inputs_min_dict[x] for x in inputs_name_list]
    _inputParams_flat_max = [inputs_max_dict[x] for x in inputs_name_list]
    n_inputs = len(_inputParams_name_flat)

    # _inputParams = list(task_dict['inputs'].keys())
    # _inputParams_len = len(_inputParams)
    # _inputParams_flat = [task_dict['inputs'][k][0] for k in _inputParams]

    # overallParams_flat = []
    # overallParams_name_flat = []
    # if(task_analyticSettings['sensitivityParams']['model']):
    #     overallParams_flat.extend(_tunableParams_flat.copy())
    #     overallParams_name_flat.extend(_tunableParams_name_flat)
    # if(task_analyticSettings['sensitivityParams']['inputs']):
    #     overallParams_flat.extend(_inputParams_flat.copy())
    #     overallParams_name_flat.extend(_inputParams_name_flat)
    #
    # overall_flat_min = [x * (1.0 - percent_range/100.) for x in overallParams_flat]
    # overall_flat_max = [x * (1.0 + percent_range/100.) for x in overallParams_flat]

    overallParams_name_flat = []
    overallParams_name_flat.extend(_tunableParams_name_flat)
    overallParams_name_flat.extend(_inputParams_name_flat)
    overall_flat_min = []
    overall_flat_min.extend(_tunableParams_flat_min)
    overall_flat_min.extend(_inputParams_flat_min)
    overall_flat_max = []
    overall_flat_max.extend(_tunableParams_flat_max)
    overall_flat_max.extend(_inputParams_flat_max)

    # To prevent singular values of min and max being the same.. move the values by +epsilon and -epsilon
    epsilon = 0.001
    overall_flat_min = [x - epsilon for x in overall_flat_min]
    overall_flat_max = [x - epsilon for x in overall_flat_max]

    # Generate the background samples with this as the Range to seed the process
    # xlimits = np.array([[0.75, 1.25], [0.75, 1.25]])
    xlimits = np.vstack([overall_flat_min, overall_flat_max]).transpose()
    sampling = LHS(xlimits=xlimits)
    x = sampling(num_background_samples)

    x_background_pd = pd.DataFrame(data=x, columns=overallParams_name_flat)
    out_samples_file_path = '%s/shap_background_samples.csv'%(dest_path_full)
    x_background_pd.to_csv(out_samples_file_path)
    file_list.append(out_samples_file_path)

    # Pick a Random Sample and (Swap with the background samples to evaluate Shap Sensitivity)
    x_base = x[0,:]



    # Define shap function for kernel explainer
    def _shap_predict(predict_array):
        n_rows = len(predict_array[:, 0])
        y_return = np.zeros((n_rows, len(x_loc)))
        # Loop through each row and extract values of scalar
        for i_row in tqdm(range(n_rows)):
            # print(predict_array[i_row,:])
            kc_scalar = predict_array[i_row, 0]
            kd_scalar = predict_array[i_row, 1]
            loc_params_dict = copy.deepcopy(params_dict)
            loc_params_dict['kc_scalar'] = kc_scalar
            loc_params_dict['kd_scalar'] = kd_scalar
            loc_output_dict = predict_func_partial(params_dict=loc_params_dict)
            # Extract the values at the final time
            loc_output_dict_endtime = loc_output_dict[-1]
            for idx, val in enumerate(x_loc_str):
                y_return[i_row, idx] = loc_output_dict_endtime[val]
        print(y_return)
        return y_return

    # Export the results

    #
    # loc_ss = SobolSensitivity(np.vstack([np.array(overall_flat_min), np.array(overall_flat_max)]),
    #                           feat_list=overallParams_name_flat,
    #                           group_map=None)
    #
    # # Generate the Saltelli Samples
    # num_samples_per_split = int(num_samples / num_splits)
    #
    # ret_dict = []
    # overall_out_array_list = []
    # for idx_delta_sample in range(num_splits):
    #     print('Generating Sample Split Group: %d / %d'%(idx_delta_sample, num_splits))
    #     calc_idx_ss = idx_delta_sample * num_samples_per_split
    #
    #     out_array = loc_ss.generate_samples_partial(n_samples=num_samples,
    #                                                 n_partial=num_samples_per_split,
    #                                                 idx_partial=calc_idx_ss)
    #
    #     overall_out_array_list.append(out_array)
    #
    # overall_out_array = np.vstack(overall_out_array_list)

    # Dump the samples to a file for the user
    temp_overall_pd = pd.DataFrame(data=overall_out_array, columns=overallParams_name_flat)
    out_samples_file_path = '%s/salitelli_samples.csv'%(dest_path_full)
    temp_overall_pd.to_csv(out_samples_file_path)
    file_list.append(out_samples_file_path)

    (nrows, ncols) = overall_out_array.shape
    print('Saltelli Sampling Size: (%d, %d)'%(nrows, ncols))
    # Convert each row into a tunable_params dict along with idx
    # the idx will be ignored if it is a scalar
    response_dict_list = []
    for cur_idx in tqdm(range(nrows)):
        model_dict_clone = copy.deepcopy(model_dict)

        # cur_idx = idx_delta_sample * nrows + cur_delta_idx

        candidate_sample_list = list(overall_out_array[cur_idx, :])

        tunableParam_dict = {
            # "idx_passthrough": cur_idx
        }
        for k, v in _tunableParams_map.items():
            tunableParam_dict[k] = list([candidate_sample_list[i] for i in v])

        model_dict_clone['analyticSettings']['tunableParams'] = tunableParam_dict

        # If inputs are part of the analysis, otherwise leave it at default
        # if (task_analyticSettings['sensitivityParams']['inputs']):
        # Compose the inputs dictionary
        inputs_dict = {}
        # the value array index is relative to the inputs.. so offset it by n_tunableParams
        for k, v in _inputParams_map.items():
            inputs_dict[k] = list([candidate_sample_list[n_tunableParams + i] for i in v])
        model_dict_clone['inputs'] = inputs_dict
        # else:
        #     model_dict_clone['inputs'] = subselect_inputs

        # Run the model for the current sample
        _loc_response_dict = _run_prediction(stub, model_dict=model_dict_clone)
        response_dict_list.append(_loc_response_dict)

    print('Evaluation of Samples completed')

    out_samples_eval_file_path = '%s/salitelli_eval.csv'%(dest_path_full)
    with open(out_samples_eval_file_path, 'w') as fp:
        json.dump(response_dict_list, fp)
    file_list.append(out_samples_eval_file_path)

    # Extract the outputs and run the sensitivity calculation using the same sobol problem
    # Assemble the outputs into a list of dictionaries so that we can convert into a PD
    consolidated_output_lod = []
    for cur_item in response_dict_list:
        # Flatten the lists by the variables
        add_item = {}
        for k, v in cur_item['prediction'].items():
            if isinstance(v, list):
                add_item[k] = v[0] # Sobol eval is done for one sample at a time
            else:
                add_item[k] = v
        consolidated_output_lod.append(add_item)

    output_pd = pd.DataFrame.from_dict(consolidated_output_lod)
    # Sort the output_pd by the idx_passThrough (and dump the
    # output_pd_sorted = output_pd.sort_values(by='idx_passthrough').set_index('idx_passthrough')

    # Output Keys
    output_keys_list = output_pd.columns # output_pd_sorted.columns
    ret_dict = {}
    for k in output_keys_list:
        ret_dict[k] = loc_ss.analyze_problem(output_pd[k].values)

    result_json_filepath_full = '%s/sensitivity_results.json'%(dest_path_full)
    with open(result_json_filepath_full, 'w') as fp:
        json.dump(ret_dict, fp)
        print('Exported: %s'%(result_json_filepath_full))
    file_list.append(result_json_filepath_full)

    meta_data_filepath_full = '%s/metadata.json'%(dest_path_full)
    meta_data_dict = {
        'metadata': ret_dict,
        'file_list': file_list
    }
    with open(meta_data_filepath_full, 'w') as fp:
        json.dump(meta_data_dict, fp)
        print('Exported: %s' % (meta_data_filepath_full))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', help='Relative path to the json file describing this model build task')
    args = parser.parse_args()

    task_json_path_full = '%s' % (args.config)
    with open(task_json_path_full, 'r') as fp:
        task_dict = json.load(fp)

    # Extract the data and model locations
    # Update it back in the task dict
    # TODO: A cleaner segregation is needed here
    rel_data_path = task_dict['analyticSettings']['rel_data_path']
    # rel_model_path = task_dict['analyticSettings']['rel_model_path']
    rel_service_path = task_dict['analyticSettings']['rel_service_path']
    pm_root_path=os.getenv('PM_ROOT_PATH',default='wd')
    with open('%s/%s/data.json'%(pm_root_path,rel_data_path), 'r') as fp:
        data_dict = json.load(fp)
    # with open('%s/model.json'%(rel_model_path), 'r') as fp:
    #     model_dict = json.load(fp)
    with open('%s/%s/metadata.json'%(pm_root_path,rel_service_path), 'r') as fp:
        service_dict = json.load(fp)

    dict_merge(task_dict, data_dict)
    # Get the model dict from the service metadata instead of a model node
    # task_dict['analyticSettings']['model'] = model_dict
    task_dict['analyticSettings']['model'] = service_dict['metadata']['model']

    run_task(task_dict,service_dict['metadata']['name'], service_dict['metadata']['port_internal'])
