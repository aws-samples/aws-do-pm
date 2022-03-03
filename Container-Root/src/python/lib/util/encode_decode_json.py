######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

import json
import base64

def utf_encode_json(json_dict):
    json_dict_str = json.dumps(json_dict)
    json_dict_bytes = json_dict_str.encode('utf-8')
    return json_dict_bytes

def utf_decode_json(json_dict_bytes):
    json_dict_str = json_dict_bytes.decode('utf-8')
    json_dict = json.loads(json_dict_str)
    return json_dict

def base64_encode_json_fname(json_fname):
    encoded_json_str = None
    with open(json_fname, 'r') as fp:
        json_dict = json.load(fp)
        json_dict_str = json.dumps(json_dict, indent=2)
        json_dict_bytes = json_dict_str.encode('utf-8')
        encoded_json_bytestr = base64.b64encode(json_dict_bytes)
        encoded_json_str = encoded_json_bytestr.decode('utf-8')
    return encoded_json_str

def base64_decode_json(encoded_json_str):
    json_decode_str = base64.b64decode(encoded_json_str)
    json_dict = json.loads(json_decode_str)
    return json_dict


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--json_fname', help='JSON File Name')

    args = parser.parse_args()

    # json_fname = 'config.json'
    encoded_json_str = base64_encode_json_fname(args.json_fname)

    env_file = 'local_env.sh'
    with open(env_file, 'w') as fp:
        fp.write('echo "Creating environment variables ENCODED_CONFIG_JSON"\n')
        fp.write('export ENCODED_CONFIG_JSON=%s\n'%(encoded_json_str))
    fp.close()
    print('Exported: local_env.sh...')
    # print('export ENCODED_CONFIG_JSON=%s'%(encoded_json_str))

    # Simply test the inversion process
    # json_dict = decode_json(encoded_json_str)
