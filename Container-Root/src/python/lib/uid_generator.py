######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

import os
import nanoid

def generate():
        uid_length_env = os.getenv('PM_ID_LENGTH', default='32')
        uid_length = int(uid_length_env)
        uid = generate_uid(uid_length)
        return uid

def generate_uid(uid_length):
        first_char = nanoid.generate('abcdefghijklmnopqrstuvwxyz', 1)
        uid_substring = nanoid.generate('abcdefghijklmnopqrstuvwxyz0123456789', uid_length-1)
        uid = '%s%s'%(first_char,uid_substring)
        return uid

if __name__ == '__main__':
        uid = generate()
        print(uid)
