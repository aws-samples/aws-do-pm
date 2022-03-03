#!/bin/sh

######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

# Unit test 2

CMD="pm config ls"

echo "$CMD"

RESULT=$(eval "$CMD")

echo "$RESULT"

echo "$RESULT" | grep PM_TO > /dev/null

if [ $? -eq 0 ]; then
	echo ""
	echo "Test2 succeeded"
else
	echo ""
	echo "Test2 failed"
fi
echo ""
