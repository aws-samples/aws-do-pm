######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

import argparse
import os
import datetime
import json
import joblib
import pandas as pd
from tqdm import tqdm
import pickle
import numpy as np
import matplotlib.pyplot as plt
import torch
from torch.autograd import Variable
from mlp import MLPRegressor
from ann_model import ANN_Model
from sklearn.model_selection import train_test_split

def build_model(analyticSettings, inputs, outputs):
    pm_root_path=os.getenv('PM_ROOT_PATH', default='wd')
    rel_dest_path = '%s/%s'%(pm_root_path,analyticSettings['rel_dest_path'])
    input_var_order = analyticSettings['input_var_order']
    output_var_order = analyticSettings['output_var_order']
    train_size = analyticSettings['train_size']
    max_epoch = analyticSettings['max_epoch']
    lr = analyticSettings['lr']
    dropout = analyticSettings['dropout']
    gpu_mode = analyticSettings['gpu_mode']

    n_input = len(input_var_order)
    n_output = len(output_var_order)

    dest_path_full = '%s' % (rel_dest_path)

    neuron_list = analyticSettings['neuron_list']
    act_fn = 'relu'

    os.makedirs(dest_path_full, exist_ok=True)

    # Assemble the scaled_x and scaled_y from the inputs and outputs
    if (isinstance(inputs, list) & isinstance(outputs, list)):
        n_input_dict = len(inputs)
        n_output_dict = len(outputs)
        input_pd_list = []
        output_pd_list = []
        for cur_input_dict in inputs:
            # Each of it has input variables with a list of values
            add_pd = pd.DataFrame()
            for k, v in cur_input_dict.items():
                add_pd[k] = np.array(v)
            input_pd_list.append(add_pd)

        for cur_output_dict in outputs:
            # Each of it has output variables with a list of values
            add_pd = pd.DataFrame()
            for k, v in cur_output_dict['actual'].items():
                add_pd[k] = np.array(v)
            output_pd_list.append(add_pd)

        input_pd = pd.concat(input_pd_list)
        output_pd = pd.concat(output_pd_list)
    elif (isinstance(inputs, dict) & isinstance(outputs, dict)):
        input_pd = pd.DataFrame()
        output_pd = pd.DataFrame()
        for k, v in inputs.items():
            input_pd[k] = np.array(v)
        for k, v in outputs['actual'].items():
            output_pd[k] = np.array(v)
    else:
        print('unrecognizeable inputs and outputs format')

    scaled_x = input_pd[input_var_order].values
    scaled_y = output_pd[output_var_order].values

    # Divide the dataset into test and train
    scaled_x_train, scaled_x_test, scaled_y_train, scaled_y_test = train_test_split(scaled_x, scaled_y, test_size=(1.0 - train_size), random_state=42)

    check_gpu_mode = torch.cuda.is_available()
    print('Host GPU Check Mode: %r' % (check_gpu_mode))
    print('Requested GPU Mode: %r' % (gpu_mode))

    target_gpu_mode = False
    if (gpu_mode & (gpu_mode == check_gpu_mode)):
        target_gpu_mode = True
    print('Target GPU Mode: %r' % (target_gpu_mode))

    mlp = MLPRegressor(n_input=n_input, n_output=n_output, hidden_layers=neuron_list, droprate=1e-6, max_epoch=max_epoch,
                       activation=act_fn, lr=lr, gpu_mode=target_gpu_mode)

    # Training, set verbose=True to see loss after each epoch.
    loss_history = mlp.fit(scaled_x_train, scaled_y_train, scaled_x_test, scaled_y_test, verbose=True)

    scaled_x_train_pt = Variable(torch.from_numpy(scaled_x_train).type(torch.FloatTensor))
    scaled_x_test_pt = Variable(torch.from_numpy(scaled_x_test).type(torch.FloatTensor))
    scaled_x_pt = Variable(torch.from_numpy(scaled_x).type(torch.FloatTensor))

    if (target_gpu_mode):
        scaled_x_train_pt = scaled_x_train_pt.cuda()
        scaled_x_test_pt = scaled_x_test_pt.cuda()
        scaled_x_pt = scaled_x_pt.cuda()

    scaled_y_train_pred = mlp.mlp_model(scaled_x_train_pt).detach().cpu().numpy()
    scaled_y_test_pred = mlp.mlp_model(scaled_x_test_pt).detach().cpu().numpy()
    scaled_y_pred = mlp.mlp_model(scaled_x_pt).detach().cpu().numpy()

    # Save torch models
    torch.save(mlp.mlp_model.model, '%s/mlp_train.pth' % (dest_path_full))

    model_history = dict()
    model_history['training loss'] = np.array([x[0] for x in loss_history])
    model_history['validation loss'] = np.array([x[1] for x in loss_history])
    pkl_file_name = os.path.join(dest_path_full + '/' + 'model_history.pkl')
    file_ptr = open(pkl_file_name, 'wb')
    pickle.dump(model_history, file_ptr)
    file_ptr.close()

    fig, ax = plt.subplots(1, 1)
    ax.plot(model_history['training loss'], 'b')
    ax.plot(model_history['validation loss'], 'r')
    ax.set_xlabel('Epochs')
    ax.set_ylabel('Loss')
    ax.legend(['Training', 'Validation'])
    plt.savefig('%s/mlp_train_epoch.png' % (dest_path_full))
    plt.close(fig)

    plt.figure(figsize=(10, 6))
    ax = plt.subplot(1, 2, 1)
    ax.plot(scaled_y_train, scaled_y_train_pred, '.')
    ax.set_xlabel('Actual')
    ax.set_ylabel('Prediction')
    ax.set_title('Train Data')
    ax.set_xlim([np.min(scaled_y), np.max(scaled_y)])
    ax.set_ylim([np.min(scaled_y), np.max(scaled_y)])
    ax = plt.subplot(1, 2, 2)
    ax.plot(scaled_y_test, scaled_y_test_pred, '.')
    ax.set_xlabel('Actual')
    ax.set_ylabel('Prediction')
    ax.set_title('Test Data')
    ax.set_xlim([np.min(scaled_y), np.max(scaled_y)])
    ax.set_ylim([np.min(scaled_y), np.max(scaled_y)])
    plt.savefig(dest_path_full + '/' + 'Actual-Vs_Predicted.png')


def export_status(task_json_path_full):
    # Export the status file
    # Export a model_details with successful state
    timestr = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    status_path_full = '%s_status.json'%(os.path.splitext(task_json_path_full)[0])
    with open(status_path_full, 'w') as fp:
        status_dict = {
            'timestamp': timestr,
            'return_status': 0
        }
        json.dump(status_dict, fp)
        print('Export task status: %s' % (status_path_full))

def extract_bias_weights(analyticSettings):
    pm_root_path = os.getenv('PM_ROOT_PATH',default='wd')
    rel_dest_path = '%s/%s'%(pm_root_path,analyticSettings['rel_dest_path'])
    gpu_mode = torch.cuda.is_available()
    layer_name = analyticSettings['layer_name']
    range_percent = analyticSettings['range_percent']

    dest_path_full = '%s' % (rel_dest_path)
    model_filepath_full = '%s/mlp_train.pth' % (dest_path_full)

    print('Initializing: %s' % (model_filepath_full))
    mlp_pt = ANN_Model(model_filepath_full, gpu_mode)

    weights_np, bias_np = mlp_pt.get_layer_weights_bias(layer_name=layer_name)
    # Modifying it to handle Layers which have 2D weights
    # First we will push the bias as column
    # Then we will reshape the weights_np and stack it
    weights_np_reshape = weights_np.reshape(1, -1)
    n_bias = len(bias_np)
    n_weight = np.prod(weights_np.shape)
    bias_weight_np = np.hstack([bias_np.squeeze(), weights_np_reshape.squeeze()])
    delta_bias_weight_np = np.abs((range_percent/100.) * bias_weight_np)

    out_dict = {
        "analyticSettings": {
            "isTunable": 1,
            "model_filepath_full": model_filepath_full,
            "tunableParams": {
                "bias_weight_array": bias_weight_np.tolist()
            },
            "tunableParamsMin": {
                "bias_weight_array": (bias_weight_np - delta_bias_weight_np).tolist()
            },
            "tunableParamsMax": {
                "bias_weight_array": (bias_weight_np + delta_bias_weight_np).tolist()
            },
            "modelParams": {
                "input_var_order": analyticSettings['input_var_order'],
                "output_var_order": analyticSettings['output_var_order'],
                "bias_weight_map": {
                    layer_name : {
                        "bias": [i for i in range(n_bias)], #[0],
                        "weights": [x + n_bias for x in range(n_weight)]
                    }
                }
            }
        },
        "inputs": {},
        "outputs": {
            "prediction": {},
            "actual": {}
        },
        "filename": "mlp_train.pth",
        "description": "Artificial Neural Network model"
    }

    # Output the dictionary at the target location
    task_model_details_filepath_full = '%s/model.json' % (dest_path_full)
    with open(task_model_details_filepath_full, 'w') as fp:
        json.dump(out_dict, fp)
        print('Exported: %s' % (task_model_details_filepath_full))

    task_meta_data_filepath_full = '%s/metadata.json'%(dest_path_full)
    with open(task_meta_data_filepath_full, 'w') as fp:
        out_meta_data_dict = {
            'metadata': out_dict
        }
        json.dump(out_meta_data_dict, fp)
        print('Exported: %s' % (task_meta_data_filepath_full))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', help='Relative path to the json file describing this model build task')
    args = parser.parse_args()

    task_json_path_full = '%s' % (args.config)
    with open(task_json_path_full, 'r') as fp_main:
        task_dict = json.load(fp_main)
        analyticSettings = task_dict['analyticSettings']
        pm_root_path = os.getenv('PM_ROOT_PATH',default='wd')
        rel_src_path = '%s/%s'%(pm_root_path,analyticSettings['rel_src_path'])

        # Assemble inputs and outputs
        # Read the task details
        meta_data_json_file = '%s/metadata.json'%(rel_src_path)

        with open(meta_data_json_file, 'r') as fp:
            meta_data_json = json.load(fp)
        data_location = meta_data_json['metadata']['filename']

        data_location_full = '%s/%s'%(rel_src_path, data_location)
        with open(data_location_full, 'r') as fp:
            loc_dict = json.load(fp)

        build_model(analyticSettings=task_dict['analyticSettings'], **loc_dict)

        extract_bias_weights(analyticSettings=task_dict['analyticSettings'])

        export_status(task_json_path_full=task_json_path_full)
