######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

import os
import json
import streamlit as st
from PIL import Image
from util import collect_data_model_id_dict, load_content_schema

def app(pm_root_path):
    st.markdown('## Data')

    # https://discuss.streamlit.io/t/label-and-values-in-in-selectbox/1436/4
    data_model_id_dict = collect_data_model_id_dict(pm_root_path)
    data_id_dict = data_model_id_dict['data']

    def format_func(option):
        cur_dict = data_id_dict[option]
        ret_string = '%s %s %s %s'%(option, cur_dict.get('created_dt', ''), cur_dict.get('filename', ''), cur_dict.get('description', ''))
        return ret_string
    # option = st.selectbox("Select option", options=list(CHOICES.keys()), format_func=format_func)

    if data_id_dict:
        sel_id = st.selectbox('Select Data', options=list(data_id_dict.keys()), format_func=format_func)
        print('Selected ID: %s'%(sel_id))

        # Read the full path of collection + selected_id
        id_path_rel = 'data/%s'%(sel_id)
        id_path_full = '%s/%s'%(pm_root_path, id_path_rel)
        content_dict = load_content_schema(id_path_full)

        # Read the input_output json if it is present
        if content_dict:
            sel_file_type = st.selectbox('Select File Type', ['json_files', 'png_files'])
            sel_file = st.selectbox('Select File', content_dict[sel_file_type])

            sel_file_full = '%s/%s'%(id_path_full, sel_file)

            if (sel_file_full.endswith('.json')):
                # Read the json and write it
                with open(sel_file_full, 'r') as fp:
                    json_dict = json.load(fp)
                st.json(json_dict)
            elif (sel_file_full.endswith('.png')):
                image = Image.open(sel_file_full)
                st.image(image)
                # st.image(sel_file_full)



