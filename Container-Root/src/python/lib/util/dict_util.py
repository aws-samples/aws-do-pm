######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

from datetime import datetime
import copy
import fnmatch
import re
import lib.uid_generator as uid_generator
import os

# https://stackoverflow.com/questions/55704719/python-replace-values-in-nested-dictionary
def list_replace_value(l, old, new):
    x = []
    for e in l:
        if isinstance(e, list):
            e = list_replace_value(e, old, new)
        elif isinstance(e, dict):
            e = dict_replace_value(e, old, new)
        elif isinstance(e, str):
            e = e.replace(old, new)
        x.append(e)
    return x


def dict_replace_value(d, old, new, ignore_key_list=[]):
    x = {}
    for k, v in d.items():
        if k not in ignore_key_list:
            if isinstance(v, dict):
                v = dict_replace_value(v, old, new)
            elif isinstance(v, list):
                v = list_replace_value(v, old, new)
            elif isinstance(v, str):
                v = v.replace(old, new)
        x[k] = v
    return x

dict_count = {}
def extract_count_map(x, regex_obj, ignore_key_list=[]):
    if isinstance(x, list):
        for y in x:
            extract_count_map(y, regex_obj)
    elif isinstance(x, dict):
        for k, v in x.items():
            if k not in ignore_key_list:
                extract_count_map([v], regex_obj)
    elif isinstance(x, str):
        match_list = regex_obj.findall(x)
        if(len(match_list) > 0):
            matched_str = match_list[0]
            dict_count[matched_str] = dict_count.get(matched_str, 0) + 1

def replace_timestamp(d, old, ignore_key_list=[]):
    timestr = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    return dict_replace_value(d, old, timestr, ignore_key_list=ignore_key_list)

def dict_merge(d1, d2):
    for k in d2:
        if k in d1 and isinstance(d1[k], dict) and isinstance(d2[k], dict):
            dict_merge(d1[k], d2[k])
        else:
            d1[k] = d2[k]


def flatten_dol(inp_dict):
    ret_map = dict()
    flat_list = list()
    name_list = list()
    param_names = inp_dict.keys()

    count = 0
    for name in param_names:
        param_length = len(inp_dict[name])
        flat_list.extend(inp_dict[name])
        name_list.extend(['%s_%d'%(name, idx) for idx in range(param_length)])
        ret_map[name] = [count+i for i in range(param_length)]
        count = count + param_length
    return flat_list, name_list, ret_map

def unflatten_dol(flat_list, dict_map):
    ret_dict = {}
    for k, v in dict_map.items():
        ret_dict[k] = [flat_list[x] for x in v]
    return ret_dict

def replace_keywords(properties, ignore_key_list=[]):
        # Scan through properties, 
        # if we see a <newid#> replace it with a generated id in all property values where it appears 
        regex_str = fnmatch.translate("<newid*>")[0:-2]
        regex_obj = re.compile(regex_str)
        extract_count_map(properties, regex_obj, ignore_key_list=ignore_key_list)

        properties_updated = copy.deepcopy(properties)
        for k, v in dict_count.items():
            properties_updated = dict_replace_value(properties_updated, k, uid_generator.generate(), ignore_key_list=ignore_key_list)
        
        # Replace any <timestamp> values with the actual date/time
        properties_updated = replace_timestamp(properties_updated,"<timestamp>",ignore_key_list=ignore_key_list)

        # Replace any <pm_s3_bucket> values with the configured PM_S3_BUCKET
        pm_s3_bucket = os.getenv('PM_S3_BUCKET',default='aws-do-pm')
        properties_updated = dict_replace_value(properties_updated, '<pm_s3_bucket>', pm_s3_bucket, ignore_key_list=ignore_key_list)

        return properties_updated


# def count(x, search_str, ignore_key_list=[]):
#     if isinstance(x, list):
#         return sum(count(y, search_str) for y in x)
#     elif isinstance(x, dict):
#         for k, v in x.items():
#             if k not in ignore_key_list:
#                 return sum(count([v], search_str, ignore_key_list))
#             else:
#                 return 0
#     elif isinstance(x, str):
#         if (search_str in x):
#             return 1
#     else:
#         return 0


if __name__ == "__main__":
    dict_a = {
        'a': '/temp/<newid>',
        'b': 10,
        'd': {
            'e': '<newid1>'
        },
        'c': {
            'd': '<newid1>',
            'e': '<newid1>'
        },
        't': '<timestamp>'
    }

    import re, fnmatch
    # created from fnmatch.translate("<newid*>")
    regex_str = fnmatch.translate("<newid*>")[0:-2]
    regex_obj = re.compile(regex_str)
    # print(regex_obj.findall("test<newid0>df"))
    # print(regex_obj.findall("test<newid12>df"))

    dict_count = {}
    extract_count_map(dict_a, regex_obj)
    print(dict_count)

    dict_count = {}
    extract_count_map(dict_a, regex_obj, ignore_key_list=['c'])
    print(dict_count)

    from uid_generator import generate_uid
    dict_a_new = dict_replace_value(dict_a, '<newid>', generate_uid(10))
    print(dict_a)
    print(dict_a_new)
    print()

    dict_a_new = dict_replace_value(dict_a, '<newid1>', generate_uid(10))
    print(dict_a)
    print(dict_a_new)
    print()

    dict_a_new = dict_replace_value(dict_a, '<newid1>', generate_uid(10), ignore_key_list=['c'])
    print(dict_a)
    print(dict_a_new)
    print()

    dict_a_new = replace_timestamp(dict_a, '<timestamp>')
    print(dict_a)
    print(dict_a_new)
    print()