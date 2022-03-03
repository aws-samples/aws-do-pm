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
echo "Stopping container ${CONTAINER} on ${TO} ..."

case "${TO}" in
        "compose")
		if [ "$1" == "" ]; then
			CMD="${DOCKER_COMPOSE} -f ${COMPOSE_FILE} down"
		else
			CMD="${DOCKER_COMPOSE} -f ${COMPOSE_FILE} rm -s -f $1"
		fi
		;;
	"swarm")
		CMD="docker stack rm ${SWARM_STACK_NAME}"
		;;
	"ecs")
		COMPOSE_FILE=${ECS_COMPOSE_FILE}
		TASK_ARNS=$(aws ecs list-tasks --cluster ${ECS_CLUSTER} --query 'taskArns' --output text)
		for task in $TASK_ARNS; do
			echo "Stopping task $task ..."
			CMD="aws ecs stop-task --cluster ${ECS_CLUSTER} --task $task"
			if [ "${VERBOSE}" == "true" ]; then
	        		echo "${CMD}"
			fi
			if [ "${DRY_RUN}" == "false" ]; then
				RESULT=$(eval "${CMD}")
			fi
			TASK_DEFINITION=$(aws ecs describe-tasks --cluster ${ECS_CLUSTER} --tasks $task --query 'tasks[].taskDefinitionArn' --output text)
			CMD="aws ecs deregister-task-definition --task-definition ${TASK_DEFINITION}"
                        if [ "${VERBOSE}" == "true" ]; then
                                echo "${CMD}"
                        fi
                        if [ "${DRY_RUN}" == "false" ]; then
                                RESULT=$(eval "${CMD}")
                        fi    
		done
		if [ "${ECS_MANAGE_CLUSTER}" == "true" ]; then
			CMD="${ECS_CLI} down --force"
		else
			COMPOSE_FILE=${ECS_COMPOSE_FILE}
			CMD="${ECS_CLI} compose --file ${COMPOSE_FILE} --cluster ${ECS_CLUSTER} down"
		fi
		;;
	"kubernetes")
		CMD="${KUBECTL} delete -f ${KUBERNETES_APP_PATH}"
		;;
	"lambda")
		CMD="aws lambda delete-function --function-name ${LAMBDA_FUNCTION_NAME}"
		;;
	"batch")
		echo ""
		echo "Stopping job ${BATCH_JOB_NAME} ..."
		# Cancel SUBMITTED, PENDING or RUNNABLE jobs
		for STATUS in "SUBMITTED" "PENDING" "RUNNABLE"; do 
			JOB_IDS=$(aws batch list-jobs --job-queue ${BATCH_JOB_QUEUE_NAME} --job-status ${STATUS} --query 'jobSummaryList[*].jobId' --output text)
			if [ ! "${JOB_IDS}" == "" ]; then
				for JOB_ID in "${JOB_IDS}"; do
					echo "Cancelling job ${JOB_ID} ..."
					CMD="aws batch cancel-job --job-id ${JOB_ID} --reason 'Stopped by user'"
					if [ "${VERBOSE}" == "true" ]; then
                                		echo "${CMD}"
                        		fi
                        		if [ "${DRY_RUN}" == "false" ]; then
                                		RESULT=$(eval "${CMD}")
                        		fi	
				done
			fi
		done
		# Terminate STARTING or RUNNING jobs
		for STATUS in "STARTING" "RUNNING"; do 
			JOB_IDS=$(aws batch list-jobs --job-queue ${BATCH_JOB_QUEUE_NAME} --job-status ${STATUS} --query 'jobSummaryList[*].jobId' --output text)
			if [ ! "${JOB_IDS}" == "" ]; then
				for JOB_ID in "${JOB_IDS}"; do
					echo "Terminating job ${JOB_ID} ..."
					CMD="aws batch terminate-job --job-id ${JOB_ID} --reason 'Stopped by user'"
					if [ "${VERBOSE}" == "true" ]; then
                                		echo "${CMD}"
                        		fi
                        		if [ "${DRY_RUN}" == "false" ]; then
                                		RESULT=$(eval "${CMD}")
                        		fi	
				done
			fi
		done
		# Deregister job definitions
		REVISIONS=$(aws batch describe-job-definitions --job-definition-name ${BATCH_JOB_DEFINITION_NAME} --query 'jobDefinitions[?status==`ACTIVE`].revision' --output text)
		for REVISION in ${REVISIONS}; do	
			echo "Deregistering job definition ${BATCH_JOB_DEFINITION_NAME}:${REVISION} ..."
			CMD="aws batch deregister-job-definition --job-definition ${BATCH_JOB_DEFINITION_NAME}:${REVISION}"
			if [ "${VERBOSE}" == "true" ]; then
				echo "${CMD}"
			fi
			if [ "${DRY_RUN}" == "false" ]; then
				RESULT=$(eval "${CMD}")
			fi
		done
		if [ "${BATCH_MANAGE_COMPUTE_ENVIRONMENT}" == "true" ]; then
			JOB_QUEUE=$(aws batch describe-job-queues --job-queues ${BATCH_JOB_QUEUE_NAME} --query 'jobQueues[*].jobQueueName' --output text)
			if [ "${JOB_QUEUE}" == "${BATCH_JOB_QUEUE_NAME}" ]; then
				echo "Deleting job queue ${BATCH_JOB_QUEUE_NAME} ..."
				CMD="aws batch update-job-queue --job-queue ${BATCH_JOB_QUEUE_NAME}  --state DISABLED"
				if [ "${VERBOSE}" == "true" ]; then
					echo "${CMD}"
				fi
				if [ "${DRY_RUN}" == "false" ]; then
					RESULT=$(eval "${CMD}")
				fi
				sleep 2
				STATE=$(aws batch describe-job-queues --job-queues ${BATCH_JOB_QUEUE_NAME} --query 'jobQueues[*].state' --output text)
				while [ ! "${STATE}" == "DISABLED" ]; do
					echo "Waiting for ${BATCH_JOB_QUEUE_NAME} state to change to DISABLED ..."	
					sleep 2
					STATE=$(aws batch describe-job-queues --job-queues ${BATCH_JOB_QUEUE_NAME} --query 'jobQueues[*].state' --output text)
				done
				CMD="aws batch delete-job-queue --job-queue ${BATCH_JOB_QUEUE_NAME}"
				if [ "${VERBOSE}" == "true" ]; then
					echo "${CMD}"
				fi
				if [ "${DRY_RUN}" == "false" ]; then
					RESULT=$(eval "${CMD}")
				fi
				# Wait for job queue to be deleted
				JOB_QUEUE=$(aws batch describe-job-queues --job-queues ${BATCH_JOB_QUEUE_NAME} --query 'jobQueues[*].jobQueueName' --output text)
				while [ ! "${JOB_QUEUE}" == "" ]; do
					echo "Waiting for job queue ${JOB_QUEUE} to be deleted ..."
					sleep 2
					JOB_QUEUE=$(aws batch describe-job-queues --job-queues ${BATCH_JOB_QUEUE_NAME} --query 'jobQueues[*].jobQueueName' --output text)
				done
			fi
			COMPUTE_ENVIRONMENT=$(aws batch describe-compute-environments --compute-environments ${BATCH_COMPUTE_ENVIRONMENT_NAME} --query 'computeEnvironments[*].computeEnvironmentName' --output text)
			if [ "${COMPUTE_ENVIRONMENT}" == "${BATCH_COMPUTE_ENVIRONMENT_NAME}" ]; then
				echo "Deleting compute environment ${BATCH_COMPUTE_ENVIRONMENT_NAME} ..."
				CMD="aws batch update-compute-environment --compute-environment ${BATCH_COMPUTE_ENVIRONMENT_NAME} --state DISABLED"
				if [ "${VERBOSE}" == "true" ]; then
					echo "${CMD}"
				fi
				if [ "${DRY_RUN}" == "false" ]; then
					RESULT=$(eval "${CMD}")
				fi
				sleep 2
				STATE=$(aws batch describe-compute-environments --compute-environments ${BATCH_COMPUTE_ENVIRONMENT_NAME} --query 'computeEnvironments[*].state' --output text)
				while [ ! "${STATE}" == "DISABLED" ]; do
					echo "Waiting for ${BATCH_COMPUTE_ENVIRONMENT_NAME} state to change to DISABLED ..."	
					sleep 2
					STATE=$(aws batch describe-compute-environment --compute-environments ${BATCH_COMPUTE_ENVIRONMENT_NAME} --query 'computeEnvironments[*].state' --output text)
				done
				STATUS=$(aws batch describe-compute-environments --compute-environments ${BATCH_COMPUTE_ENVIRONMENT_NAME} --query 'computeEnvironments[*].status' --output text)
				while [ ! "${STATUS}" == "VALID" ]; do
					echo "Waiting for ${BATCH_COMPUTE_ENVIRONMENT_NAME} status to change to VALID ..."	
					sleep 2
					STATUS=$(aws batch describe-compute-environments --compute-environments ${BATCH_COMPUTE_ENVIRONMENT_NAME} --query 'computeEnvironments[*].status' --output text)
				done
				CMD="aws batch delete-compute-environment --compute-environment ${BATCH_COMPUTE_ENVIRONMENT_NAME}"
			fi
		else
			CMD=""
		fi
		;;
	*)
                checkTO "${TO}"
		CMD="docker container rm -f ${CONTAINER}"
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

