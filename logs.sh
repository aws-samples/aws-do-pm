#!/bin/bash

######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

source .env

if [ "${DEBUG}" == "true" ]; then
        set -x
fi

if [ ! "$TO" == "$PM_TO" ]; then
	        echo $PM_TO > wd/.to
		        source .env
fi

echo ""
echo "Showing logs on ${TO} ..."

case "${TO}" in
        "compose")
		if [ "$1" == "" ]; then
			CMD="${DOCKER_COMPOSE} -f ${COMPOSE_FILE} logs -f"
		else
			SERVICE_NAME=$1
			CONTAINER_INDEX=$2
			if [ "$CONTAINER_INDEX" == "" ]; then
				CONTAINER_INDEX=1
			fi
			CMD="docker logs -f ${COMPOSE_PROJECT_NAME}${DOCKER_COMPOSE_SEP}${SERVICE_NAME}${DOCKER_COMPOSE_SEP}${CONTAINER_INDEX}"
		fi
		;;
	"swarm")
		if [ "$1" == "" ]; then
			CMD="docker service logs -f ${SWARM_STACK_NAME}_${SWARM_SERVICE_NAME}"
		else
			CMD="docker service ps ${SWARM_STACK_NAME}_${SWARM_SERVICE_NAME} | grep ${SWARM_SERVICE_NAME}.$1 | cut -d ' ' -f 1 | xargs docker service logs -f"
		fi	
		;;
	"ecs")
		CONTAINER_INDEX=1
		if [ ! "$1" == "" ]; then
			CONTAINER_INDEX=$1
		fi
		CMD="${ECS_CLI} logs --task-id $(./status.sh | grep RUNNING | head -n ${CONTAINER_INDEX} | tail -n 1 | cut -d '/' -f 2) --follow"
		;;
	"kubernetes")
		CMD="${KUBETAIL} ${APP_NAME} -n ${NAMESPACE} -s 30m"
		;;
	"lambda")
		since="--since 1h"
		if [ ! "$1" == "" ]; then
			since="--since $1"
		fi
		CMD="aws logs tail ${since} --follow /aws/lambda/${LAMBDA_FUNCTION_NAME}"
		;;
	"batch")
		if [ "$1" == "" ]; then
			JOB_IDS_RUNNING=$(aws batch list-jobs --job-queue ${BATCH_JOB_QUEUE_NAME} --job-status RUNNING --query 'jobSummaryList[*].jobId' --output text)
			JOB_IDS_SUCCEEDED=$(aws batch list-jobs --job-queue ${BATCH_JOB_QUEUE_NAME} --job-status SUCCEEDED --query 'jobSummaryList[*].jobId' --output text)
			JOB_IDS_FAILED=$(aws batch list-jobs --job-queue ${BATCH_JOB_QUEUE_NAME} --job-status FAILED --query 'jobSummaryLists[*].jobId' --output text)
			JOB_IDS="$JOB_IDS_RUNNING $JOB_IDS_SUCCEEDED $JOB_IDS_FAILED"
		else
			JOB_IDS="$@"
		fi
		for JOB_ID in ${JOB_IDS}; do
			if [ ! "$JOB_ID" == "None" ]; then
				echo ""
				echo "Getting log evewnts for job ${JOB_ID} ..."
				LOG_STREAM=$(aws batch describe-jobs --jobs ${JOB_ID} --query 'jobs[*].container.logStreamName' --output text)
				CMD="aws logs get-log-events --log-group-name /aws/batch/job --no-paginate --query 'events[*].{timestamp:timestamp,message:message}' --output text --log-stream-name ${LOG_STREAM}"
				if [ "${VERBOSE}" == "true" ]; then
        				echo "${CMD}"
				fi
				if [ "${DRY_RUN}" == "false" ]; then
        				eval "${CMD}"
				fi
			fi
		done
		CMD=""
		;;
	*)
                checkTO "${TO}"
		CMD="docker container logs -f ${CONTAINER}"
		;;
esac

if [ "${VERBOSE}" == "true" ]; then
        echo "${CMD}"
fi

if [ "${DRY_RUN}" == "false" ]; then
        eval "${CMD}"
fi

if [ "${DEBUG}" == "true" ]; then
        set +x
fi
