#!/bin/bash

######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

source .env
source .fun2

function usage() {
	echo ""
	echo "Usage:"
	echo "    $0 [option] - builds one or more containers in this project."
        echo ""
	echo "                  The build behavior is controlled by settings  "
	echo "                  in the configuration file .env"
	echo ""
	echo "                  BUILD_TO -       controls whether the build is run by docker or docker-compose"
	echo "                                   use './config.sh BUILD_TO docker' or './config.sh BUILD_TO compose' to set"
	echo "                                   BUILD_TO=docker is recommended since it can build all container images"
	echo "                                   BUILD_TO=compose will only build the platform and ui container image "
	echo ""
	echo "       options when BUILD_TO=docker:"
	echo "            ''         - build the last built Dockerfile"
	echo "            ls         - list available Dockerfiles to build"
	echo "            all        - build all Dockerfiles sequentially"
	echo ""
}

if [ ! "$TO" == "$BUILD_TO" ]; then
	echo $BUILD_TO > wd/.to
	source .env
fi

if [ "${DEBUG}" == "true" ]; then
        set -x
fi

if [ "$1" == "--help" ]; then
	usage
else

	echo ""
	echo "Building container image(s) ..."

	case "${TO}" in 
		"compose")
			echo " ... using ${DOCKER_COMPOSE}"
			generate_compose_files
			CMD="${DOCKER_COMPOSE} -f ${COMPOSE_FILE} build"
			;;
		"docker")
			echo " ... using docker"
			if [ "$1" == "ls" ]; then
				ls -alh Dockerfile-*
			elif [ "$1" == "all" ]; then
				DOCKERFILES=$(ls Dockerfile-*)
				for DF in $DOCKERFILES; do
					./build.sh $DF
				done	
			elif [ ! "$1" == "" ]; then
				echo ""
				echo "=================================================="
				echo "Building Dockerfile: $1"
				DF_EXT=-$(echo ${1} | cut -d '-' -f 2)
				echo ${DF_EXT} > wd/.dockerfile_ext
				./build.sh
			else
				CMD="docker image build ${BUILD_OPTS} -t ${REGISTRY}${IMAGE}${TAG} ."
			fi
			;;
		*)
			echo ""
			echo "Target orchestrator (TO) must be 'compose' or 'docker' to build"
			echo "Please set target orchestrator to 'compose' or 'docker' by executing ./config.sh TO "
			usage
			;;
	esac
fi

if [ "${VERBOSE}" == "true" ]; then
	echo "${CMD}"
fi
if [ "${DRY_RUN}" == "false" ]; then
	eval "${CMD}"
fi

if [ "${DEBUG}" == "true" ]; then
        set +x
fi
