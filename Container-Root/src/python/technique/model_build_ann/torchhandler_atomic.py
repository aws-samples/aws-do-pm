######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

import numpy as np
import torch
from torch.autograd import Variable
from mlpmanual_pt import MLPManual_PT


def initialize(model_loc, gpu_mode, **kwargs):
    print('Initializing: %s' % (model_loc))
    mlp_pt = MLPManual_PT(model_loc, gpu_mode)
    print(mlp_pt.named_modules)

    ret_dict = {
        'mlp_pt': mlp_pt,
        'gpu_mode': gpu_mode
    }
    return ret_dict


# inp_dict has
# analyticSettings & inputs
def run(mlp_pt, gpu_mode, inp_dict):
    analyticSettings = inp_dict['analyticSettings']
    inputs = inp_dict['inputs']
    bias_weight_array = None

    # Extract the weight_bias_map from modelParams
    bias_weight_map = analyticSettings['modelParams']['bias_weight_map']

    # Override with any values present in the tunableParams
    if "tunableParams" in analyticSettings:
        if "bias_weight_array" in analyticSettings['tunableParams']:
            bias_weight_array = np.array(analyticSettings['tunableParams']['bias_weight_array']).astype(np.float32)
            for layer_name, weight_bias in bias_weight_map.items():
                if 'weights' in weight_bias:
                    loc_array = bias_weight_array[np.array(weight_bias['weights'])]
                    mlp_pt.set_layer_weights(layer_name=layer_name, weights_np=loc_array.reshape(1, -1))
                if 'bias' in weight_bias:
                    loc_array = bias_weight_array[np.array(weight_bias['bias'])]
                    mlp_pt.set_layer_bias(layer_name=layer_name, bias_np=loc_array.reshape(1, -1))

    # Assemble the x_pred as numpy and convert it to a torch object running on a GPU
    # Use the modelParams input_var_order to assemble an array
    input_var_order = analyticSettings['modelParams']['input_var_order']
    n_cols = len(input_var_order)
    n_rows = len(inputs[input_var_order[0]])
    x_pred = np.zeros((n_rows, n_cols))
    for idx, cur_var in enumerate(input_var_order):
        x_pred[:, idx] = np.array(inputs[cur_var])
        # inputs_array_list.append(inputs[cur_var])
    print('Forward Pass: %s'%(str(x_pred.shape)))
    if (gpu_mode):
        x_pred_pt = Variable(torch.from_numpy(x_pred).type(torch.FloatTensor)).cuda()
    else:
        x_pred_pt = Variable(torch.from_numpy(x_pred).type(torch.FloatTensor)).cpu()

    # Forward call detaches and converts to numpy
    out_pred_update = mlp_pt.forward(x_pred_pt)

    ret_dict = {}
    output_var_order = analyticSettings['modelParams']['output_var_order']
    for idx, cur_var in enumerate(output_var_order):
        ret_dict[cur_var] = out_pred_update[:, idx].tolist()

    return ret_dict

def cleanup(**kwargs):
    return

