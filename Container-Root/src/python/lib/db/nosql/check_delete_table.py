######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

from dynamodb_access import DynamoDBAccess

if __name__ == "__main__":
    loc_dynamodb_access = DynamoDBAccess()
    loc_dynamodb_access.check_delete_db_table()
