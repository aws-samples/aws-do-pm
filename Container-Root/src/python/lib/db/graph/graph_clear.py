######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

import lib.db.graph.dba as dba
import os

if __name__ == "__main__":
    graphdb_name = os.getenv('PM_GRAPHDB_NAME', default='pm')
    graphdb_id = os.getenv('PM_GRAPHDB_ID', default='pm')
    graphdb_cr = os.getenv('PM_GRAPHDB_CR', default='pm')
    graphdb_graph = os.getenv('PM_GRAPHDB_GRAPH', default='pm')
    db = dba._create_get_db(graphdb_name,graphdb_id,graphdb_cr)
    graph = dba._create_get_graph(graphdb_graph,db)
    dba._delete_collections(graph)