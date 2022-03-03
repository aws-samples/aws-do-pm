#!/bin/bash

######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

endpoint="http://localhost"
if [ ! -z "$1" ]; then
        endpoint="$1"
fi

CMD="curl -i -s ${endpoint}/say?text=This%20is%20a%20Docker%20container%20running%20in%20ECS%21"

echo "$CMD"

RESULT=$(eval "$CMD")

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
