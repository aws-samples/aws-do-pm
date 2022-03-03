#!/bin/bash

######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

. ./.env 

if [ "${DEBUG}" == "true" ]; then
	set -x
fi

function usage
{
	echo ""
	echo "Usage: $0 [setting] [value]"
	echo ""
	echo "   $0 --help             - display usage information"
	echo "   $0 --show             - show the values of all settings"
	echo "   $0 --show [setting]   - show the value of the specified setting"
	echo "   $0 -i                 - edit selected settings interactively"
	echo "   $0                    - edit configuration file"
	echo "   $0 setting            - edit specified setting interactively"
	echo "   $0 setting value      - set the specified setting to the provided value"
	echo ""
}

if [ "$1" == "--help" ]; then
	usage
	CMD=""
elif [ "$1" == "--show" ]; then
	if [ "$2" == "" ]; then
		env
	else
		eval echo \$$2
	fi
elif [ "$1" == "-i" ]; then
	./config.sh TO
	./config.sh BASE_IMAGE_PATH
	./config.sh IMAGE_NAME
	./config.sh VERSION
elif [ "$1" == "" ]; then
	CMD="${CMD_EDIT} .env"
else
	if [ "$2" == "" ]; then
		# Interactive
		echo ""
		cat ./.env | grep "^export $1=" -B 10
		echo ""
		CURRENT_VALUE=$(printenv $1)
		echo "Set $1 [ ${CURRENT_VALUE} ] to: " 
		read NEW_VALUE
		if [ "${NEW_VALUE}" == "" ]; then
			NEW_VALUE="${CURRENT_VALUE}"
		fi
	else
		# Set value to $2
		NEW_VALUE="$2"
	fi
	if [ "$1" == "REGISTRY" ]; then
		CMD=""
		echo "${NEW_VALUE}" > ${PM_ROOT_PATH}/.registry
	elif [ "$1" == "AWS_ACCESS_KEY_ID" ]; then
		CMD=""
		echo "${NEW_VALUE}" > ${PM_ROOT_PATH}/.aws_id
	elif [ "$1" == "AWS_SECRET_ACCESS_KEY" ]; then
		CMD=""
		echo "${NEW_VALUE}" > ${PM_ROOT_PATH}/.aws_cr
	elif [ "$1" == "PM_GRAPHDB_SYSTEM_CR" ]; then
		CMD=""
		echo "${NEW_VALUE}" > ${PM_ROOT_PATH}/.graphdb_system_cr
	elif [ "$1" == "PM_GRAPHDB_ID" ]; then
		CMD=""
		echo "${NEW_VALUE}" > ${PM_ROOT_PATH}/.graphdb_id
	elif [ "$1" == "PM_GRAPHDB_CR" ]; then
		CMD=""
		echo "${NEW_VALUE}" > ${PM_ROOT_PATH}/.graphdb_cr
	elif [ "$1" == "PM_S3_BUCKET" ]; then
		CMD=""
		echo "${NEW_VALUE}" > ${PM_ROOT_PATH}/.s3b
	elif [ "$1" == "PV_TYPE" ]; then
		CMD=""
		echo "${NEW_VALUE}" > ${PM_ROOT_PATH}/.pv_type
	elif [ "$1" == "EFS_VOLUME_ID" ]; then
		CMD=""
		echo "${NEW_VALUE}" > ${PM_ROOT_PATH}/.efs
	elif [ "$1" == "ALB_ALLOW_CIDRS" ]; then
		CMD=""
		echo "${NEW_VALUE}" > ${PM_ROOT_PATH}/.allow
	elif [ "$1" == "PM_PLATFORM_SCALE" ]; then
		CMD=""
		echo "${NEW_VALUE}" > ${PM_ROOT_PATH}/.platform
	elif [ "$1" == "KCFG_ENC" ]; then
		CMD=""
		echo "NEW_VALUE is:"
		echo "${NEW_VALUE}"
		echo "${NEW_VALUE}" > ${PM_ROOT_PATH}/.kcfg
	else
		CMD="cp -f ./.env ./.env.bak; cat ./.env | sed \"s#^export $1=.*#export $1=${NEW_VALUE}#\" | tee ./.env > /dev/null; echo ''; if [ "$VERBOSE" == "true" ]; then echo New value:; cat ./.env | grep \"^export $1=\"; fi"
	fi
fi


if [ "${VERBOSE}" == "true" ]; then
	echo ""
	echo "${CMD}"
fi

if [ "${DRY_RUN}" == "false" ]; then
	eval "${CMD}"
	echo ""
fi

if [ "${DEBUG}" == "true" ]; then
	set +x
fi

