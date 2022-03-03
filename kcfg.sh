#!/bin/bash

######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

. .env

function usage {
	echo ""
	echo "Usage $0 [kubeconfig_path]      - configure pm platform for access to Kubernetes"
	echo ""
	echo "          kubeconfig_path       - optional location of the kube config file to encode"
	echo "                                  default: ~/.kube/config"
	echo ""
}

if [ "$1" == "--help" ]; then
	usage
else
	KCFG=~/.kube/config
	if [ ! "$1" == "" ]; then
	       KCFG=$1
	fi
	if [ "$OPERATING_SYSTEM" == "Linux" ]; then	       
		./pm config set KCFG_ENC $(cat ${KCFG} | base64 -w 0) 
	elif [ "$OPERATING_SYSTEM" == "MacOS" ]; then
		./pm config set KCFG_ENC $(cat ${KCFG} | base64 -b 0)
	else
		echo "Not implemented for current operating system $OPERATING_SYSTEM"
	fi
fi

