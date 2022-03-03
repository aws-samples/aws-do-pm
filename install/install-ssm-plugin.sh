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

echo ""
echo "Installing SSM plugin on $OPERATING_SYSTEM ..."
echo ""

if [ "$OPERATING_SYSTEM" == "Linux" ]; then
	command -v apt-get &> /dev/null
	APT_COMMAND=$?
	command -v yum &> /dev/null
	YUM_COMMAND=$?
	if [ "${APT_COMMAND}" == "0" ]; then
		curl "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/ubuntu_64bit/session-manager-plugin.deb" -o "session-manager-plugin.deb"
		sudo dpkg -i session-manager-plugin.deb
		#rm -f ./session-manager-plugin.deb
	elif [ "${YUM_COMMAND}" == "0" ]; then
		curl "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/linux_64bit/session-manager-plugin.rpm" -o "session-manager-plugin.rpm"
		sudo yum install -y session-manager-plugin.rpm
		#rm -f ./session-manager-plugin.rpm
	else
		echo "Unable to determine proper session manager plugin package for your OS"
	fi
elif [ "$OPERATING_SYSTEM" == "MacOS" ]; then
	curl "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/mac/sessionmanager-bundle.zip" -o "sessionmanager-bundle.zip"
	unzip sessionmanager-bundle.zip
	sudo ./sessionmanager-bundle/install -i /usr/local/sessionmanagerplugin -b /usr/local/bin/session-manager-plugin
	rm -f ./sessionmanager-bundle.zip
else
	echo "Operating system $OPERATING_SYSTEM not supported"
fi


