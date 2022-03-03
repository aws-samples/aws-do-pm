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
echo "Showing status on target orchestrator ${TO} ..."

case "${TO}" in
	"compose")
		#CMD="${DOCKER_COMPOSE} -f ${COMPOSE_FILE} ps -a"
		CMD="docker ps -a | grep ${APP_NAME}"
		;;
	"swarm")
		CMD="docker stack ps ${SWARM_STACK_NAME}"
		;;
	"ecs")
		COMPOSE_FILE=${ECS_COMPOSE_FILE}
		CMD="${ECS_CLI} ps"
		if [ "${VERBOSE}" == "true" ]; then
			echo ""
	        	echo "${CMD}"
		fi
		if [ "${DRY_RUN}" == "false" ]; then
	        	eval "${CMD}"
		fi
		CMD="aws ecs describe-tasks --cluster ${ECS_CLUSTER} --query 'tasks[*].{TaskArn:taskArn,State:lastStatus,Health:healthStatus,LaunchType:launchType,PrivateIP:containers[0].networkInterfaces[0].privateIpv4Address}' --output table --tasks $(aws ecs list-tasks --cluster ${ECS_CLUSTER} --query 'taskArns' --output text)"
		;;
	"kubernetes")
		CMD="${KUBECTL} -n ${NAMESPACE} get pods"
		;;
	"lambda")
		CMD="aws lambda get-function --function-name ${LAMBDA_FUNCTION_NAME} --query '{Name:Configuration.FunctionName,State:Configuration.State,Status:Configuration.LastUpdateStatus,Updated:Configuration.LastModified,Image:Code.ImageUri}' --output table"
		;;
	"batch")
		if [ "$1" == "" ]; then
			STATUS_LIST=(SUBMITTED PENDING RUNNABLE STARTING RUNNING SUCCEEDED FAILED)
			for STATUS in ${STATUS_LIST[@]}; do
				CMD="aws batch list-jobs --job-queue ${BATCH_JOB_QUEUE_NAME} --job-status ${STATUS} --query 'jobSummaryList[*].{createdAt:createdAt,jobId:jobId,jobName:jobName,status:status,statusReason:statusReason,exitCode:container.exitCode}' --output table"
				if [ "${VERBOSE}" == "true" ]; then
					echo ""
	        			echo "${CMD}"
				fi
				if [ "${DRY_RUN}" == "false" ]; then
	        			eval "${CMD}"
				fi
			done
			CMD=""
		else
			CMD="aws batch describe-jobs --jobs $@ --query 'jobs[*].{createdAt:createdAt,jobId:jobId,jobName:jobName,status:status,statusReason:statusReason,exitCode:container.exitCode,platformCapabilities:platformCapabilities[0]}' --output table"
		fi
		;;
	*)
		checkTO "${TO}"
		CMD="docker ps -a | grep ${CONTAINER}"
		;;
esac

if [ "${VERBOSE}" == "true" ]; then
	echo ""
        echo "${CMD}"
fi

if [ "${DRY_RUN}" == "false" ]; then
        eval "${CMD}"
fi

if [ "${DEBUG}" == "true" ]; then
        set +x
fi

