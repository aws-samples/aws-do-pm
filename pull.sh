#!/bin/bash

######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

source .env

function usage(){
	echo ""
	echo "Usage: $0 [arg] - pull one or more images from the configured registry"
	echo ""
	echo "      arg:"
	echo ""
	echo "        ''      - pull the latest built image only"
	echo "        ls      - list available images to pull"
        echo "        all     - pull all project images"
	echo "        image   - pull specified image only"
	echo ""
}

if [ "$1" == "--help" ]; then
	usage
	exit 0
fi

if [ "$1" == "" ]; then
	docker image push ${REGISTRY}${IMAGE}${TAG}
else
	case "$1" in 
		"ls")
			aws ecr describe-repositories | grep repositoryUri | grep $IMAGE_NAME | cut -d '"' -f 4
			;;
		"all")
			IMAGES=$(aws ecr describe-repositories | grep repositoryUri | grep $IMAGE_NAME | cut -d '"' -f 4)
			for IMG in $IMAGES; do
				docker pull ${IMG}${TAG}
			done
			;;
		*)
			docker pull ${1}${TAG}
			;;
	esac
fi
