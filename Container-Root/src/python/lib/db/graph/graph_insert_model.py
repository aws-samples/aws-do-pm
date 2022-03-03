######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

import lib.db.graph.dba as dba
import lib.db.graph.data as data 
import argparse

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--data-id', help='Preprocessed data ID')
    parser.add_argument('--model-id', help='Model ID')
    args = parser.parse_args()
    data_ID = args.data_id
    model_ID = args.model_id

    graph = dba.get_graph()
    properties = {"seq_id": 0, "path": "model/%s"%model_ID}
    data.insert_vertex('model',model_ID,properties,graph)
    data.insert_edge('model_data','data/%s'%(data_ID),'model/%s'%(model_ID),graph)

    
