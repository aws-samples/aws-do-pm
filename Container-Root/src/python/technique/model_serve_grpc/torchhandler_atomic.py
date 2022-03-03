######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

import numpy as np
import pandas as pd
from tqdm import tqdm
import torch
from torch.autograd import Variable
from ann_model import ANN_Model


def initialize(model_loc, gpu_mode, **kwargs):
    print('Initializing: %s' % (model_loc))
    cuda_available = torch.cuda.is_available()
    print('CUDA available? %s'%cuda_available)
    effective_gpu_mode = gpu_mode & cuda_available
    print('Effective GPU Mode: %s'%effective_gpu_mode)
    mlp_pt = ANN_Model(model_loc, gpu_mode)
    print(mlp_pt.named_modules)

    ret_dict = {
        'mlp_pt': mlp_pt,
        'gpu_mode': effective_gpu_mode
    }
    return ret_dict


# inp_dict has
# analyticSettings
# inputs
def run(mlp_pt, gpu_mode, inp_dict):
    analyticSettings = inp_dict['analyticSettings']
    inputs = inp_dict['inputs']
    bias_weight_array = None

    # Extract the weight_bias_map from modelParams
    bias_weight_map = analyticSettings['modelParams']['bias_weight_map']
    # if "bias_weight_array" in analyticSettings['modelParams']:
    #     bias_weight_array = np.array(analyticSettings['modelParams']['bias_weight_array']).astype(np.float32)

    # Override with any values present in the tunableParams
    if "tunableParams" in analyticSettings:
        if "bias_weight_array" in analyticSettings['tunableParams']:
            bias_weight_array = np.array(analyticSettings['tunableParams']['bias_weight_array']).astype(np.float32)
            for layer_name, weight_bias in bias_weight_map.items():
                # Extract the size of the weights and bias
                (loc_weight_array, loc_bias_array) = mlp_pt.get_layer_weights_bias(layer_name=layer_name)
                if 'weights' in weight_bias:
                    loc_array = bias_weight_array[np.array(weight_bias['weights'])]
                    # Reshape the array to the correct size of the weights array
                    mlp_pt.set_layer_weights(layer_name=layer_name, weights_np=loc_array.reshape(loc_weight_array.shape))
                if 'bias' in weight_bias:
                    loc_array = bias_weight_array[np.array(weight_bias['bias'])]
                    mlp_pt.set_layer_bias(layer_name=layer_name, bias_np=loc_array.reshape(1, -1))

    # Assemble the x_pred as numpy and convert it to a torch object running on a GPU
    # inputs = analyticSettings['inputs']
    # Use the modelParams input_var_order to assemble an array
    input_var_order = analyticSettings['modelParams']['input_var_order']
    n_cols = len(input_var_order)
    n_rows = len(inputs[input_var_order[0]])
    x_pred = np.zeros((n_rows, n_cols))
    for idx, cur_var in enumerate(input_var_order):
        x_pred[:, idx] = np.array(inputs[cur_var])
        # inputs_array_list.append(inputs[cur_var])
    # x_pred = np.hstack(inputs_array_list)
    # x_pred = np.array(inputs['x_pred'])
    print('Forward Pass: %s'%(str(x_pred.shape)))
    if (gpu_mode):
        x_pred_pt = Variable(torch.from_numpy(x_pred).type(torch.FloatTensor)).cuda()
    else:
        x_pred_pt = Variable(torch.from_numpy(x_pred).type(torch.FloatTensor))

    # Forward call detaches and converts to numpy
    out_pred_update = mlp_pt.forward(x_pred_pt)

    ret_dict = {}
    output_var_order = analyticSettings['modelParams']['output_var_order']
    for idx, cur_var in enumerate(output_var_order):
        ret_dict[cur_var] = out_pred_update[:, idx].tolist()

    return ret_dict

    #
    # ret_dict = {
    #     'y': out_pred_update.tolist()
    # }
    #
    # return ret_dict


def cleanup(**kwargs):
    return


if __name__ == "__main__":
    import os

    model_loc = os.getenv('MODEL_LOC')
    print('Initializing w/:%s' % (model_loc))
    gpu_mode = torch.cuda.is_available()
    init_dict = initialize(model_loc=model_loc, gpu_mode=gpu_mode)

    inp_dict = {}

    loc_analyticSettings = {}
    loc_analyticSettings['modelParams'] = {
        "input_var_order": ["x_1", "x_2", "x_3"],
        "output_var_order": ["y_1"],
        # "bias_weight_array": list(np.ones((5,))),
        "bias_weight_map": {
            "final": {
                "weights": [1, 2, 3, 4],
                "bias": [0]
            }
        }
    }
    loc_analyticSettings['tunableParams'] = {
        "bias_weight_array": list(np.random.random(5, ))
    }

    # Set the Inputs
    n_rows = 10
    inputs = {}
    for idx, cur_var in enumerate(loc_analyticSettings['modelParams']['input_var_order']):
        inputs[cur_var] = np.random.random(n_rows).tolist()
    #
    # inputs = {
    #     "x_pred": list(np.random.random((10, 3)))
    # }

    inp_dict['analyticSettings'] = loc_analyticSettings
    inp_dict['inputs'] = inputs

    print('Simulating')
    ret_dict = run(inp_dict=inp_dict,
                   **init_dict)

    print(ret_dict)

    print('Clean Up')
    cleanup(**init_dict)
