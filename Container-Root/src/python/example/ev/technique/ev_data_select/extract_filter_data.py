######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

import argparse
import json
import os
import numpy as np
import matplotlib.pyplot as plt
import datetime
import time

if __name__ == '__main__':
    time.sleep(14) # allow container to start Running
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', help='Relative path to the json file describing this model build task')
    args = parser.parse_args()

    task_json_path_full = '%s'%(args.config)
    
    print("Executing data selection task: %s ..."%task_json_path_full)
    
    pm_root_path = os.getenv('PM_ROOT_PATH', default='wd')
    with open(task_json_path_full, 'r') as fp1:
        task_dict = json.load(fp1)
        analyticSettings = task_dict['analyticSettings']
        rel_src_path = analyticSettings['rel_src_path']
        full_src_path = '%s/%s'%(pm_root_path,rel_src_path)
        rel_dest_path = analyticSettings['rel_dest_path']
        full_dest_path = '%s/%s'%(pm_root_path,rel_dest_path)

        # Assemble inputs and outputs
        # Read the task details
        meta_data_json_file = '%s/metadata.json'%(full_src_path)

        with open(meta_data_json_file, 'r') as fp2:
            meta_data_json = json.load(fp2)
        meta_data_list = meta_data_json['metadata']['list']
        print('Len of Data sets: %d' % (len(meta_data_list)))

        # Pick the nodes that have a certain metadata
        filter_condition = analyticSettings['filter_condition']
        print(filter_condition)
        data_meta_list = [x for x in meta_data_list if dict(x, **filter_condition) == x]
        print('Len of Filtered Data: %d' % (len(data_meta_list)))

        inputs_list = []
        outputs_list = []
        for cur_data_meta in data_meta_list:
            data_location = cur_data_meta['dataLocation']
            data_location_full = '%s/%s'%(full_src_path, data_location)
            with open(data_location_full, 'r') as fp3:
                loc_dict = json.load(fp3)
            inputs_list.append(loc_dict['inputs'])
            outputs_list.append(loc_dict['outputs'])

        input_keys = list(inputs_list[0].keys())
        output_keys = list(outputs_list[0]['actual'].keys())

        # Dataset has only actual measurements
        # Loop through the list and create an overall single dictionary for prediction
        overall_input = {k:[] for k in input_keys}
        overall_actual_output = {k:[] for k in output_keys}
        for cur_input, cur_output in zip(inputs_list, outputs_list):
            for k, v in cur_input.items():
                overall_input[k].extend(v)
            for k, v in cur_output['actual'].items():
                overall_actual_output[k].extend(v)

        overall_dict = {
            'inputs': overall_input,
            'outputs': {
                'prediction': [],
                'actual': overall_actual_output
            }
        }

        # Export the data into a json file
        os.makedirs(full_dest_path, exist_ok=True)
        data_file_full = '%s/data.json'%(full_dest_path)
        with open(data_file_full, 'w') as fp4:
            json.dump(overall_dict, fp4)
            fp4.flush()
            os.fsync(fp4.fileno())
            print('Exported Data: %s'%(data_file_full))
        fp4.close()

        # Generate a plot with the inputs and outputs
        n_rows_input_plot = len(input_keys)
        fig, ax = plt.subplots(n_rows_input_plot, 1, figsize=(10, 4), sharex=True)
        for idx_plot, cur_input_key in enumerate(input_keys):
            ax[idx_plot].plot(np.arange(len(overall_input[cur_input_key])), overall_input[cur_input_key], linestyle='--', marker='.')
            ax[idx_plot].set_ylabel(cur_input_key)
            ax[idx_plot].grid()
        fig.savefig(full_dest_path + '/input_data_plot.png')
        plt.close(fig)

        n_rows_output_plot = len(output_keys)
        fig, ax = plt.subplots(n_rows_output_plot, 1, figsize=(10, 4), sharex=True)
        for idx_plot, cur_output_key in enumerate(output_keys):
            if(n_rows_output_plot > 1):
                cur_ax = ax[idx_plot]
            else:
                cur_ax = ax
            cur_ax.plot(np.arange(len(overall_actual_output[cur_output_key])), overall_actual_output[cur_output_key], linestyle='--', marker='.')
            cur_ax.set_ylabel(cur_output_key)
            cur_ax.grid()
        fig.savefig(full_dest_path + '/output_data_plot.png')
        plt.close(fig)


        meta_data_file_full = '%s/metadata.json'%(full_dest_path)
        with open(meta_data_file_full, 'w') as fp5:
            m=analyticSettings
            m['filename'] = 'data.json'
            m['description'] = 'Selected EV data with filter %s '%(filter_condition)
            meta_data_dict = {
                'created_dt': datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'),
                'metadata': m
            }
            json.dump(meta_data_dict, fp5)
            fp5.flush()
            os.fsync(fp5.fileno())
            print('Exported Data: %s'%(meta_data_file_full))
        
        fd = os.open(full_dest_path, os.O_RDONLY)
        os.fsync(fd)
        os.close(fd)
