######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

from arango import ArangoClient
import os

db_url = os.getenv('PM_GRAPHDB_URL','http://graphdb:8529')
client = ArangoClient(hosts=db_url)

def _create_get_vertex_collection(in_graph, in_vertex_collection_str, verbose=True):
    if not in_graph.has_vertex_collection(in_vertex_collection_str):
        if verbose:
            print('Creating Vertex Collection: %s'%(in_vertex_collection_str))
        return in_graph.create_vertex_collection(in_vertex_collection_str)
    else:
        if verbose:
            print('Fetching Vertex Collection: %s'%(in_vertex_collection_str))
        return in_graph.vertex_collection(in_vertex_collection_str)

def _create_get_edge_definition(in_graph, in_edge_collection_str, from_vertex_collections, to_vertex_collections, verbose=True):
    if not in_graph.has_edge_definition(in_edge_collection_str):
        if verbose:
            print('Creating Edge Collection: %s'%(in_edge_collection_str))
        return in_graph.create_edge_definition(edge_collection = in_edge_collection_str,
                                               from_vertex_collections = from_vertex_collections,
                                               to_vertex_collections = to_vertex_collections)
    else:
        if verbose:
            print('Fetching Edge Collection: %s'%(in_edge_collection_str))
        return in_graph.edge_collection(in_edge_collection_str)

def _create_get_db(in_dbname, in_username, in_password, verbose=False):
    graphdb_system_cr=os.getenv('PM_GRAPHDB_SYSTEM_CR', default='root')
    sys_db = client.db("_system", username="root", password=graphdb_system_cr)
    if not sys_db.has_database(in_dbname):
        if verbose:
            print('Creating Database: %s'%in_dbname)
        sys_db.create_database(in_dbname)
    if not sys_db.has_user(in_username):
        if verbose:
            print('Creating user %s'%in_username) 
        sys_db.create_user(username=in_username, password=in_password, active=True)

    sys_db.update_permission(username=in_username, permission='rw', database=in_dbname)

    db = client.db(in_dbname, username=in_username, password=in_password)
    return db
    
def get_db():
    db_name=os.getenv('PM_GRAPHDB_NAME', default='pm')
    db_user=os.getenv('PM_GRAPHDB_ID', default='root')
    db_pass=os.getenv('PM_GRAPHDB_CR', default='root')
    db = _create_get_db(db_name, db_user, db_pass)
    return db

def _create_get_graph(in_graphname, db, verbose=False):
    if not db.has_graph(in_graphname):
        if verbose:
            print('Creating graph: %s'%in_graphname)
        graph = db.create_graph(in_graphname)
    else:
        if verbose:
            print('Fetching graph: %s'%in_graphname)
        graph = db.graph(in_graphname)
    return graph

def get_graph():
    db = get_db()
    graph_name = os.getenv('PM_GRAPHDB_GRAPH', default='pm')
    graph = _create_get_graph(graph_name,db)
    return graph

def _delete_collection(in_collection_name, db, verbose=True):
    if verbose:
        print('Deleting Collection: %s'%(in_collection_name))
    db.delete_collection(in_collection_name)

def _delete_edge_collections(graph, verbose=False):
    edge_collection_list = graph.edge_definitions()
    for cur_collection in edge_collection_list:
        if verbose:
            print('Deleting Edge Collection: %s'%(cur_collection['edge_collection']))
        graph.delete_edge_definition(name=cur_collection['edge_collection'], purge=True)

def _delete_vertex_collections(graph, verbose=True):    
    vertex_collection_list = graph.vertex_collections()
    for cur_collection_name in vertex_collection_list:
        try:
            if verbose:
                print('Deleting Vertex Collection: %s'%(cur_collection_name))
            graph.delete_vertex_collection(name=cur_collection_name, purge=True)
        except:
            if verbose:
                print('Exception Raised, Continuing')

def _delete_collections(graph):
    _delete_edge_collections(graph)
    _delete_vertex_collections(graph)
