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

if [ "$OPERATING_SYSTEM" == "Linux" ]; then
	echo "Installing ecs-cli on Linux ..."
	sudo curl -Lo /usr/local/bin/ecs-cli https://amazon-ecs-cli.s3.amazonaws.com/ecs-cli-linux-amd64-latest
	gpg --import ./gpg-public-key
	curl -Lo ecs-cli.asc https://amazon-ecs-cli.s3.amazonaws.com/ecs-cli-linux-amd64-latest.asc
	gpg --verify ecs-cli.asc /usr/local/bin/ecs-cli
	sudo chmod +x /usr/local/bin/ecs-cli
	ecs-cli --version
elif [ "$OPERATING_SYSTEM" == "MacOS" ]; then
	echo "Installing ecs-cli on MacOS ..."
	sudo curl -Lo /usr/local/bin/ecs-cli https://amazon-ecs-cli.s3.amazonaws.com/ecs-cli-darwin-amd64-latest
	brew install gnupg
	gpg --import ./gpg-public-key
	curl -Lo ecs-cli.asc https://amazon-ecs-cli.s3.amazonaws.com/ecs-cli-darwin-amd64-latest.asc
	gpg --verify ecs-cli.asc /usr/local/bin/ecs-cli
	sudo chmod +x /usr/local/bin/ecs-cli
	ecs-cli --version
else
	echo "Unrecognized OS $OPERATING_SYSTEM"
fi


