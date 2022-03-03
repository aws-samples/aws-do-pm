#!/bin/bash

######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

# Install grpcurl
curl -L -o grpcurl.tar.gz https://github.com/fullstorydev/grpcurl/releases/download/v1.8.5/grpcurl_1.8.5_linux_x86_64.tar.gz && \
gunzip ./grpcurl.tar.gz && \
tar xvf grpcurl.tar && \
mv ./grpcurl /usr/local/bin && \
mv LICENSE /usr/local/bin/grpcurl-LICENSE && \
rm -rf grpcurl.tar
