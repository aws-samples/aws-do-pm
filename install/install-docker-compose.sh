#!/bin/bash

######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

if [ -e .env ]; then
        . .env
elif [ -e ../.env ]; then
        pushd ..
        . .env
        popd
elif [ -e /app/pm/.env ]; then
        pushd /app/pm
        . .env
        popd
fi

os
if [ "$OPERATING_SYSTEM" == "Linux" ]; then
	echo "Installing docker-compose on Linux ..."
	curl -L "https://github.com/docker/compose/releases/download/1.29.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
	chmod +x /usr/local/bin/docker-compose
	docker-compose --version
elif [ "$OPERATING_SYSTEM" == "MacOS" ]; then
	echo "Docker-compose on MacOS is included in Docker Desktop. Please refer to https://docs.docker.com/docker-for-mac/install"	
else
        echo "Unrecognized OS $OPERATING_SYSTEM"
fi
