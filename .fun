#!/bin/bash

######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

# do framework helper functions

## Detect current operating system
function os
{
        UNAME=$(uname -a)
        if [ "$(echo $UNAME | awk '{print $1}')" == "Darwin" ]; then
                export OPERATING_SYSTEM="MacOS"
        elif [ "$(echo $UNAME | awk '{print $1}')" == "Linux" ]; then
                export OPERATING_SYSTEM="Linux"
        elif [ "${UNAME:0:5}" == "MINGW" ]; then
                export OPERATING_SYSTEM="Windows"
                export MSYS_NO_PATHCONV=1 # turn off path conversion
        else
                export OPERATING_SYSTEM="Other"
        fi
}
## End os function
os

## Determine current host IP address
function hostip
{
	case "${OPERATING_SYSTEM}" in
        "Linux")
                export HOST_IP=$(hostname -I | tr " " "\n" | head -1) # Linux
                ;;
        "MacOS")
                export HOST_IP=$(ifconfig | grep -v 127.0.0.1 | grep -v inet6 | grep inet | head -n 1 | awk '{print $2}') # Mac OS
                ;;
        "Windows")
                export HOST_IP=$( ((ipconfig | grep IPv4 | grep 10.187 | tail -1) && (ipconfig | grep IPv4 | grep 3. | head -1)) | tail -1 | awk '{print $14}' ) # Git bash
                ;;
        *)
                export HOST_IP=$(hostname)
                ;;
	esac
}
## End hostip function 
hostip

## Check default target orchestrator
function checkTO
{
	KNOWN_TARGET_ORCHESTRATORS="docker compose ecs swarm kubernetes lambdalocal lambda batchlocal batch"
	echo "${KNOWN_TARGET_ORCHESTRATORS}" | grep $1 > /dev/null
	if [ "$?" == "1" ]; then
		echo ""
		echo "Supported target orchestrators:"
		echo "${KNOWN_TARGET_ORCHESTRATORS}"
		echo "WARNING: Unrecognized target orchestrator TO=$1. Defaulting to docker."
		echo ""
	fi	
}

## Return first available port starting with arg, return 0 if no port is available
function firstAvailable()
{
	if [ "$1" == "" ]; then
		PORT_DESIRED=80
	else
		PORT_DESIRED=$1
	fi
	PORT_AVAILABLE=${PORT_DESIRED}
	LOCAL_ORCHESTRATORS="docker compose lambdalocal batchlocal"
	TO_IS_LOCAL=$(echo ${LOCAL_ORCHESTRATORS} | grep -w -q ${TO}; echo $?)
	if [ "${TO_IS_LOCAL}" == "0" ]; then
		TEST_RESULT=$(timeout 1 bash -c "</dev/tcp/localhost/${PORT_AVAILABLE}" 1>/dev/null 2>/dev/null; echo $?)
		while [ "${TEST_RESULT}" == "0" ]; do
			PORT_AVAILABLE=$((PORT_AVAILABLE+1))
			if [ "${PORT_AVAILABLE}" -ge "65535" ]; then
				PORT_AVAILABLE="0"
				break
			fi
			TEST_RESULT=$(timeout 1 bash -c "</dev/tcp/localhost/${PORT_AVAILABLE}" 1>/dev/null 2>/dev/null; echo $?)
		done
	fi
	echo "${PORT_AVAILABLE}"
}

