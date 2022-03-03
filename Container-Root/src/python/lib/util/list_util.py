######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

def splitWords(l):
    for words in l:
        if '{' not in words:
            yield from words.split()
        else:
            yield words

def unique_list(input_list):
    unique = set(input_list)
    return list(unique)

def flatten_list_of_lists(list_of_lists):
    ret_list = []
    for l in list_of_lists:
        ret_list.extend(l)
    return ret_list

def diff_lists(a,b):
    sa = set(a)
    sb = set(b)
    sd = sa.difference(sb)
    return list(sd)

if __name__ == '__main__':
    
    l_dict = {
        "spec": {
            "template": {
                "spec": {
                    "containers": [
                        {"name": "abc",
                         "volume": "efg"
                         }
                        ]
                }
            }
        }
    }
    
    import json
    l1 = json.dumps(l_dict)
    
    l2 = ["one", "two three", l1, "four five", "six"]

    print(list(splitWords(l2)))    