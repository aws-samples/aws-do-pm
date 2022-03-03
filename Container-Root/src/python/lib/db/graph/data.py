######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

import lib.util.dict_util as dict_util

def insert_vertex(collection_name, vertex_id, properties, graph):
    vertex_collection = graph.vertex_collection(collection_name)
    properties["_key"]=vertex_id
    #data.insert({"_key": vertex_id, "seq_id": properties['seq_id'], "path": properties['path']})
    vertex_collection.insert(properties)

def insert_edge(edge_collection_name, from_element, to_element, graph):
    edge_collection = graph.edge_collection(edge_collection_name)
    edge_collection.insert({"_from": from_element, "_to": to_element})

def get_vertex(collection_name, vertex_id, graph):
    vertex_collection = graph.vertex_collection(collection_name)
    return vertex_collection.get(vertex_id)

def get_vertex_parent_ids(collection_name,vertex_id,graph,verbose=True):
    parent_ids=[]
    start_vertex='%s/%s'%(collection_name,vertex_id)
    traversal=graph.traverse(start_vertex, direction='inbound', strategy='bfs', edge_uniqueness='global', vertex_uniqueness='global',min_depth=1,max_depth=1)
    parent_vertices=traversal['vertices']
    for vertex in parent_vertices:
        parent_ids.append(vertex['_id'])
    if verbose:
        print(parent_ids)
    return parent_ids

def update_vertex(collection_name, vertex_id, properties, graph):
    vertex_collection = graph.vertex_collection(collection_name)
    vertex = vertex_collection.get(vertex_id)
    dict_util.dict_merge(vertex,properties)
    vertex_collection.update(vertex)

def find_vertex(collection_name, field_name, field_value, graph, skip=0, limit=100):
    vertex_collection=get_vertices(collection_name,graph)
    cursor = vertex_collection.find({field_name: field_value}, skip, limit)
    match = [x for x in cursor]
    return match    

def find_vertex_key(collection_name, field_name, field_value, graph, skip=0, limit=100):
    vertices = find_vertex(collection_name,field_name,field_value,graph,skip,limit)
    ids=[]
    for v in vertices:
        ids.append(v["_key"])
    return ids 

def get_edge(edge_collection_name, edge_id, graph):
    edge_collection = graph(edge_collection_name)
    return edge_collection.get(edge_id)

def get_vertices(collection_name, graph):
    vertex_collection=None
    if graph.has_vertex_collection(collection_name):
        vertex_collection = graph.vertex_collection(collection_name)
    return vertex_collection
