######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

import lib.db.graph.dba as dba
import lib.db.graph.data as data 
import argparse

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--data_id', help='Data ID')
    args = parser.parse_args()
    data_ID = args.data_id

    graph = dba.get_graph()
    properties = {"seq_id": 0, "path": "data/%s"%data_ID}
    data.insert_vertex('rawdata',data_ID,properties,graph)

