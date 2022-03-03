#!/bin/bash

######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

payload=$(echo '{"text": "This is a Docker container running as a lambda function!"}' | base64 -w 0)

RESULT=$(./exec.sh ${payload})

echo "$RESULT"

echo "$RESULT" | grep Docker > /dev/null

if [ $? -eq 0 ]; then
        echo ""
        echo "Test2 succeeded"
else
        echo ""
        echo "Test2 failed"
fi
echo ""
