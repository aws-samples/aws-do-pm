#!/bin/bash

######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

source .env
source .fun2

if [ "${DEBUG}" == "true" ]; then
	set -x
fi

if [ -z "$1" ]; then
	MODE="-d"
else
	MODE="-it"
fi 

if [ ! "$TO" == "$PM_TO" ]; then
        echo $PM_TO > wd/.to
        source .env
fi

echo ""
echo "Running container ${CONTAINER} on ${TO} ..."

case "${TO}" in
	"compose")
		generate_compose_files
		CMD="${DOCKER_COMPOSE} -f ${COMPOSE_FILE} up -d $1"
		;;
	"swarm")
		generate_compose_files
		CMD="docker stack deploy -c ${COMPOSE_FILE} ${SWARM_STACK_NAME}"
		;;
	"ecs")
		prepare_ecs_roles
		prepare_ecs_cluster
		generate_compose_files
		COMPOSE_FILE=${ECS_COMPOSE_FILE}
		CMD="${ECS_CLI} compose --ecs-params ${ECS_PARAMS_FILE} --file ${ECS_COMPOSE_FILE} create --launch-type ${ECS_LAUNCH_TYPE}"
		if [ "${VERBOSE}" == "true" ]; then
			echo "${CMD}"
		fi

		if [ "${DRY_RUN}" == "false" ]; then
			TASK_DEFINITION_RESULT=$(eval "${CMD}")
			echo ""
		fi
		CMD="aws ecs run-task --cluster ${ECS_CLUSTER} --task-definition compose --enable-execute-command --launch-type ${ECS_LAUNCH_TYPE}"
	        if [ "${ECS_LAUNCH_TYPE}" == "FARGATE" ]; then
			CMD="$CMD --network-configuration \"awsvpcConfiguration={subnets=[${SUBNET_ID}],securityGroups=[${SG_ID}],assignPublicIp=${ECS_ASSIGN_PUBLIC_IP}}\""
		fi
		;;
	"kubernetes")
		cp -f to/kubernetes/template/012-pvc.${PV_TYPE} to/kubernetes/template/012-pvc.yaml	
		generate_kubernetes_manifests
		CMD="${KUBECTL} -n ${NAMESPACE} apply -f ${KUBERNETES_APP_PATH}"
		;;
	"lambdalocal")
		CMD="docker run ${RUN_OPTS} ${CONTAINER_NAME} ${MODE} ${NETWORK} -p ${PORT_EXTERNAL}:8080 ${REGISTRY}${IMAGE}${TAG} $@"
		;;
	"lambda")
		generate_lambda_files
		prepare_lambda_role
		sleep 5 # wait for lambda role to finish creating
		CMD="aws lambda create-function --region ${REGION} --function-name ${LAMBDA_FUNCTION_NAME} --package-type Image --code ImageUri=${REGISTRY}${IMAGE}${TAG} --role ${LAMBDA_ROLE_ARN}"
		;;
	"batchlocal")
		if [ "$1" == "" ]; then
			BATCH_COMMAND=${BATCH_COMMAND_DEFAULT}
		else
			BATCH_COMMAND="$@"
		fi
		CMD="docker container run ${RUN_OPTS} ${CONTAINER_NAME} -d ${NETWORK} ${VOL_MAP} ${REGISTRY}${IMAGE}${TAG} ${BATCH_COMMAND}"
		;;
	"batch")
		prepare_ecs_roles
		prepare_batch_compute_environment
		prepare_batch_queue
		register_batch_job_definition "$@"
		CMD="aws batch submit-job --job-name ${BATCH_JOB_NAME} --job-queue ${BATCH_JOB_QUEUE_NAME} --job-definition ${BATCH_JOB_DEFINITION_NAME}"
		;;
	*)
		checkTO "${TO}"
		CMD="docker container run ${RUN_OPTS} ${CONTAINER_NAME} ${MODE} ${NETWORK} ${PORT_MAP} ${VOL_MAP} ${REGISTRY}${IMAGE}${TAG} $@"
		;;
esac

if [ "${VERBOSE}" == "true" ]; then
	echo "${CMD}"
fi

if [ "${DRY_RUN}" == "false" ]; then
	RESULT=$(eval "${CMD}")
	if [ "$TO" == "kubernetes" ]; then
		./ecr-login.sh
	fi
	echo ""
fi

if [ "${DEBUG}" == "true" ]; then
	set +x
fi
