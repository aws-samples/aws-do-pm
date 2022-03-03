######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

import os
import streamlit as st
# st.set_page_config(layout="wide")

import render_data
import render_model

pm_root_path = os.getenv('PM_ROOT_PATH', default='wd')

pages = {'data':render_data.app, 'model': render_model.app}
choice = st.sidebar.radio("Choose your page: ",tuple(pages.keys()))
pages[choice](pm_root_path)