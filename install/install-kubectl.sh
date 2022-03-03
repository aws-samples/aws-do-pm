#!/bin/bash

######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

# Install kubectl
#curl -o kubectl https://amazon-eks.s3.us-west-2.amazonaws.com/1.21.5/2021-01-05/bin/linux/amd64/kubectl
curl -o kubectl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x ./kubectl
mv ./kubectl /usr/local/bin
kubectl version --client
