######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

import lib.db.graph.dba as dba
import lib.db.graph.data as graphdata
import os
import json
from datetime import datetime

if __name__ == "__main__":
    graphdb_name = os.getenv('PM_GRAPHDB_NAME', default='pm')
    graphdb_id = os.getenv('PM_GRAPHDB_ID', default='pm')
    graphdb_cr = os.getenv('PM_GRAPHDB_CR', default='pm')
    graphdb_graph = os.getenv('PM_GRAPHDB_GRAPH', default='pm')
    db = dba._create_get_db(graphdb_name, graphdb_id, graphdb_cr)
    graph = dba._create_get_graph(graphdb_graph, db)

    technique = dba._create_get_vertex_collection(graph, 'technique')
    data = dba._create_get_vertex_collection(graph, 'data')
    model = dba._create_get_vertex_collection(graph, 'model')
    service = dba._create_get_vertex_collection(graph, 'service')
    asset = dba._create_get_vertex_collection(graph, 'asset')
    task = dba._create_get_vertex_collection(graph, 'task')
    error = dba._create_get_vertex_collection(graph, 'error')
    trash = dba._create_get_vertex_collection(graph, 'trash')
    user = dba._create_get_vertex_collection(graph, 'user')

    link = dba._create_get_edge_definition(graph, 'link', ['technique','data','model','asset','task','user'], ['technique','data','model','asset','task','error','user'])

    # add root node - technique registration without a task
    with open('/src/python/lib/db/graph/root_technique_registration.json', 'r') as fp:
        technique_registration_graphdb_properties = json.load(fp)

    dt = datetime.now()
    dts = dt.strftime("%Y%d%m-%H%M%S-%f")

    technique_registration_graphdb_properties["created_dt"] = dts
    technique_id=technique_registration_graphdb_properties["technique_id"]
    graphdata.insert_vertex('technique',technique_id,technique_registration_graphdb_properties,graph)

    # add default user
#    with open('/src/python/lib/db/graph/user_default.json', 'r') as fp:
#        user_properties = json.load(fp)
#    user_id = user_properties['user_id']
#    graphdata.insert_vertex('user',user_id,user_properties,graph)