#!/bin/bash

######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

RESULT=$(./exec.sh)

echo "$RESULT"

echo "$RESULT" | grep Healthy > /dev/null

if [ $? -eq 0 ]; then
        echo ""
        echo "Test1 succeeded"
else
        echo ""
        echo "Test1 failed"
fi
echo ""
