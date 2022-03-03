######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

import os
import json

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


if __name__ == "__main__":
    st.set_page_config(layout='wide')
    st.title('PM Dashboard')

    data_model_id_dict = collect_data_model_id_dict()

    # Reference imp
    dict_keys = list(data_model_id_dict.keys())
    sel_dict_key = st.sidebar.selectbox('Select Collection Type', dict_keys)
    print('Selected Collection: %s'%(sel_dict_key))
    sel_id = st.sidebar.selectbox('Select ID', data_model_id_dict[sel_dict_key])
    print('Selected ID: %s'%(sel_id))

    # Read the full path of collection + selected_id
    id_path_rel = '%s/%s'%(sel_dict_key, sel_id)
    id_path_full = '%s/%s'%(pm_root_path, id_path_rel)
    content_dict = load_content_schema(id_path_full)

    # Show Meta Data
    st.markdown('### Metadata')
    st.json(content_dict['metadata'])

    # Loop through the png files
    if (len(content_dict['png_files']) > 0):
        sel_png_file = st.sidebar.selectbox('Select PNG File', content_dict['png_files'])
        st.image('%s/%s'%(id_path_full, sel_png_file))

    # If there is a filename in the metadata
    if 'filename' in content_dict['metadata']:
        # Load the filename and use it for interactive plots
        with open('%s/%s'%(id_path_full, content_dict['metadata']['filename'])) as fp:
            inp_out_dict = json.load(fp)



