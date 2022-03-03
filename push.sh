#!/bin/bash

######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

source .env

function usage(){
	echo ""
	echo "Usage: $0 [arg] - push one or more images to the configured registry"
	echo ""
	echo "      arg:"
	echo ""
	echo "        ''      - push the latest build image only"
	echo "        ls      - list available images to push"
        echo "        all     - push all project images"
	echo "        image   - push specified image"
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
			docker images | grep $IMAGE_NAME | grep $REGISTRY | grep $VERSION		
			;;
		"all")
			IMAGES=$(docker images | grep $IMAGE_NAME | grep $REGISTRY | grep $VERSION | cut -d ' ' -f 1)
			for IMG in $IMAGES; do
				docker push ${IMG}${TAG}
			done
			;;
		*)
			docker push ${1}${TAG}
			;;
	esac
fi
