#!/bin/bash

######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

source .env

function usage(){
	echo ""
	echo "Usage: $0 [service_name] [local_port_number] - expose a service locally through port forwarding"
	echo ""
	echo "      service_name       - name of service to expose (ui|grapdb), default: ui"
	echo "      local_port_number  - local port number to forward to the service port, default: ${PM_UI_PORT_INT}"
	echo ""
}

if [ "$1" == "--help" ]; then
	usage
	exit 0
fi

if [ "${QUIET}" == "true" ]; then
	VERBOSE=false
fi

if [ "${DEBUG}" == "true" ]; then
        set -x
fi

if [ ! "$TO" == "$PM_TO" ]; then
	echo $PM_TO > wd/.to
	source .env
fi

if [ "${VERBOSE}" == "true" ]; then
	echo ""
	echo "Executing command on orchestrator ${TO} ..."
fi

case "${TO}" in
        "compose")
		if [ "${COMPOSE_CONTEXT_TYPE}" == "moby" ]; then
			echo ""
			echo "Services are already exposed locally"
			CMD="./status.sh"
		elif [ "${COMPOSE_CONTEXT_TYPE}" == "ecs" ]; then
			echo ""
			echo "Expose of container running on ECS is not supported"
			echo ""
		else
			echo ""
			echo "Unrecognized COMPOSE_CONTEXT_TYPE ${COMPOSE_CONTEXT_TYPE}"
			echo "Supported context types are moby | ecs"
		fi
		;;
	"kubernetes")
		SERVICE_NAME=$1
		if [ "$1" == "" ]; then
			SERVICE_NAME=ui
		fi
                SERVICE_PORT=$2
                if [ "$2" == "" ]; then
                        SERVICE_PORT=$PM_UI_PORT_INT
                fi
		if [ "$SERVICE_NAME" == "graphdb" ]; then
			SERVICE_PORT_INT=$PM_GRAPHDB_PORT_INT
		elif [ "$SERVICE_NAME" == "ui" ]; then
			SERVICE_PORT_INT=$PM_UI_PORT_INT
		else
			echo ""
			echo "Unrecognized service name: $SERVICE_NAME"
			echo ""
		fi
		CMD="kubectl port-forward $(kubectl get pods | grep ${SERVICE_NAME} | head -n 1 | tail -n 1 | cut -d ' ' -f 1 ) ${SERVICE_PORT}:${SERVICE_PORT_INT}"
		;;
	*)
		echo ""
		echo "Expose operation is not supported for target orchestrator ${TO}"
		echo ""
		usage
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

