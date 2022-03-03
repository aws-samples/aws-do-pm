#!/bin/bash

######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

source .env

function usage {
	echo ""
	echo "Usage: $0 <container_name> <instance_num> <src_path> <dest_path> - copies container:<src_path> to local <dest_path>"
	echo ""
}

if [ "${QUIET}" == "true" ]; then
	VERBOSE=false
fi

if [ "${DEBUG}" == "true" ]; then
        set -x
fi

if [ "$TO" == "docker" ]; then
	echo $PM_TO > wd/.to
	source .env
fi

if [ "${VERBOSE}" == "true" ]; then
	echo ""
	echo "Executing command on orchestrator ${TO} ..."
fi

SRC_PATH=$3
if [ "$SRC_PATH" == "" ]; then
	echo ""
	echo "Please specify source path"
	usage
	exit 1
fi
DEST_PATH=$4
if [ "$DEST_PATH" == "" ]; then
	echo ""
	echo "Please specify destination path within target container"
	usage
	exit 1
fi

case "${TO}" in
        "compose")
		if [ "${COMPOSE_CONTEXT_TYPE}" == "moby" ]; then
			SERVICE_NAME=$1
			if [ "$SERVICE_NAME" == "" ]; then
				SERVICE_NAME=platform
			fi
			CONTAINER_INDEX=$2
			if [ "$CONTAINER_INDEX" == "" ]; then
				CONTAINER_INDEX=1
			fi
			CMD="docker cp ${COMPOSE_PROJECT_NAME}_${SERVICE_NAME}_${CONTAINER_INDEX}:${SRC_PATH} ${DEST_PATH}"
		elif [ "${COMPOSE_CONTEXT_TYPE}" == "ecs" ]; then
			echo ""
			echo "Copy to container running on ECS is not supported"
			echo ""
		else
			echo ""
			echo "Unrecognized COMPOSE_CONTEXT_TYPE ${COMPOSE_CONTEXT_TYPE}"
			echo "Supported context types are moby | ecs"
		fi
		;;
	"swarm")
		SERVICE_INDEX=$1
		if [ "$SERVICE_INDEX" == "" ]; then
			SERVICE_INDEX=1
		fi
		TASK_ID=${SWARM_STACK_NAME}_${SWARM_SERVICE_NAME}.${SERVICE_INDEX}
		CONTAINER_ID=$(docker ps | grep ${TASK_ID} | cut -d ' ' -f 1)
		if [ "${CONTAINER_ID}" == "" ]; then
			CONTAINER_HOST=$(docker service ps ${SWARM_STACK_NAME}_${SWARM_SERVICE_NAME} -f desired-state=running --format="{{.Node}} {{.Name }} {{.ID}}" | grep ${TASK_ID} | cut -d ' ' -f 1)
			echo ""
			if [ "${CONTAINER_HOST}" == "" ]; then
				echo "Could not find running task ${TASK_ID}"
			else
				echo "Cannot connect to service task ${TASK_ID}"
				echo "Only connections to tasks running on the local host are supported"
				echo "You may connect to the node running this task ($CONTAINER_HOST) and use docker exec locally"
				echo " or configure remote docker daemon access." 
			fi
			echo ""
			CMD=""
		else
			CMD="docker cp ${CONTAINER_ID}:${SRC_PATH} ${DEST_PATH}"
		fi
		;;
	"ecs")
		echo ""
		echo "Copy operation is not supported for target orchestrator $TO"
		;;
	"kubernetes")
		POD_GROUP=$1
		if [ "$1" == "" ]; then
			POD_GROUP=platform
		fi
                CONTAINER_INDEX=$2
                if [ "$2" == "" ]; then
                        CONTAINER_INDEX=1
                fi
		POD_CMD="${@:3}"
		if [ "$POD_CMD" == "" ]; then
			POD_CMD=bash
		fi
		CMD="unset DEBUG; ${KUBECTL} -n ${NAMESPACE} cp $( ${KUBECTL} -n ${NAMESPACE} get pod | grep ${POD_GROUP} | head -n ${CONTAINER_INDEX} | tail -n 1 | cut -d ' ' -f 1 ):${SRC_PATH} ${DEST_PATH}"
		;;
	"lambda")
		echo ""
		echo "Copy operation is not supported for target orchestrator $TO"
		exit 1
		;;
	"batch")
		echo ""
		echo "Copy operation is not supported for target orchestrator $TO"
		exit 1
		;;
	*)
		checkTO "${TO}"
		echo "Copy operatio is not supported for target orchestrator $TO"
		exit 1
		;;
esac

if [ "${VERBOSE}" == "true" ]; then
        echo "${CMD}"
	echo ""
fi

if [ "${DRY_RUN}" == "false" ]; then
        eval "${CMD}"
fi

if [ "${DEBUG}" == "true" ]; then
        set +x
fi

