######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

import os
import json
import streamlit as st
from pm.data.data import list_data
from pm.model.model import list_model

def collect_data_model_id_dict(pm_root_path):
    # Fetch all the tags from the PM_ROOT_PATH

    data_id_list, data_id_map = list_data(verbose=False)
    model_id_list, model_id_map = list_model(verbose=False)
    ret_dict = {
        'data': data_id_map,
        'model': model_id_map
    }
    return ret_dict


def load_content_schema(id_path):
    ret_dict = {}
    file_list = os.listdir(id_path)

    # Extract the metadata
    if (len(file_list) > 0):
        if 'metadata.json' in file_list:
            with open('%s/metadata.json'%(id_path)) as fp:
                metadata_dict = json.load(fp)
            ret_dict['metadata'] = metadata_dict['metadata']
        else:
            ret_dict['metadata'] = {}
        # jsonfile
        ret_dict['json_files'] = [x for x in file_list if x.endswith('.json')]
        # pngfiles
        ret_dict['png_files'] = [x for x in file_list if x.endswith('.png')]

    return ret_dict