######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

import json
import os

def read_line(filepath):
    line=''
    with open(filepath,'r') as fp:
        line = fp.readline()
    line=line.rstrip('\n')
    return line

def read_json(filepath):
    dict={}
    with open(filepath, 'r') as fp:
        dict = json.load(fp)
    return dict

def write_json(filepath,dict):
    with open(filepath, 'w') as fp:
        json.dump(dict,fp)
        fp.flush()
        os.fsync(fp.fileno())
    fp.close()