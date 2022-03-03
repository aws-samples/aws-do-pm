#!/bin/bash

######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

endpoint="http://localhost"
if [ ! -z "$1" ]; then
	endpoint="$1"
fi

CMD="curl -i -s ${endpoint}"

echo "$CMD"

RESULT=$(eval "$CMD")

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
