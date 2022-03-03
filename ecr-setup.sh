#!/bin/bash

######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

source .env

function usage(){
	echo ""
	echo "Usage: $0       - creates a repository for each pm docker images so it may be pushed to ECR"
	echo ""
}

if [ "$1" == "--help" ]; then
	usage
	exit 0
fi

REPOSITORIES=$(aws ecr describe-repositories | jq .repositories[].repositoryUri)
echo ""
echo "Existing repositories:"
echo "$REPOSITORIES"
echo ""

IMG_EXTENSIONS=$(ls Dockerfile-* | sed -e 's/Dockerfile-//g')
for IMG_EXT in ${IMG_EXTENSIONS} ; do
	echo ""
	IMG=${IMAGE_NAME}-${IMG_EXT}
	echo "Checking repository for image $IMG ..."
	EXISTS=$( echo "${REPOSITORIES}" | grep ${IMG} )
	if [ "$?" == "0" ]; then
		echo "Repository ${REGISTRY}${IMG} already exists"
	else
		echo "Creating repository ${REGISTRY}${IMG} ..."
		aws ecr create-repository --repository-name ${IMG}
	fi
done

