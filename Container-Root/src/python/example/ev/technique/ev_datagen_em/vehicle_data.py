######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

# Vehicle Characteristics
vehicle_dict_ref = {
    "unladen_wt_lbs": 10000,
    "scaler": {
        "cd": 1,
        "frontal_area": 1,
        "rolling_resistance": 1
    }
}

# Battery discharge characteristic from a Spec Speet
battery_dict = {
    'num_cells': 30000,
    'capacity': 12.16,
    'v': [4.75, 4.5, 4.4, 4.3, 4.2, 4.1, 4.05, 4.0, 3.8, 3.7, 2.0],
    'D_Wh': [0, 0.4, 1.0, 2.0, 3.0, 4.0, 4.2, 4.6, 4.7, 4.8, 5.0]
}
