#!/bin/bash

######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

curl -o /tmp/kubetail https://raw.githubusercontent.com/johanhaleby/kubetail/master/kubetail
chmod +x /tmp/kubetail
mv /tmp/kubetail /usr/local/bin/kubetail

