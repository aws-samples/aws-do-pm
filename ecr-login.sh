#!/bin/bash

######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

source .env

function usage(){
	echo ""
	echo "Usage: $0       - creates a registry secret in Kubernetes using the locally configured AWS CLI credentials"
	echo ""
}

if [ "$1" == "--help" ]; then
	usage
	exit 0
fi

# Delete regcred if it already exists
kubectl delete secret --ignore-not-found regcred -n ${NAMESPACE}

# Create regcred
kubectl create secret docker-registry regcred \
  --docker-server=${REGISTRY} \
  --docker-username=AWS \
  --docker-password=$(aws ecr get-login-password) \
  --namespace=${NAMESPACE}
