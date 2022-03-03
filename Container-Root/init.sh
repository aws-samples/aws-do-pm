#!/bin/bash

######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

# Initialize container. This script can be called either upon startup, or on-demand

# Configure ~/.kube/config if needed
if [ ! -d ~/.kube ]; then
	mkdir -p ~/.kube
fi
if [ ! -f ~/.kube/config ]; then
	if [ ! "$KCFG_ENC" == "" ]; then
        	echo "${KCFG_ENC}" | base64 -d > ~/.kube/config
        fi
fi
