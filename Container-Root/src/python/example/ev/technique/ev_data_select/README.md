# Data Selection Module

The data selection module demonstrates the structure of a custom technique that consumes a registered dataset and extracts a subset of data using a filtering logic.

## JSON Contract
The json contract for the task is shown below. 

<li> The input_artifact points to the source data at data/<id> </li>
<li> The output artifact points to the target data that would have extracted, transformed from the source dataset </li>
<li> The analytic settings has the arguments and values for the python program that performs the ETL </li>

```
{
    "task_name": "ev_data_select",
    "technique_name": "ev_data_select",
    "analyticSettings": {
        "rel_src_path": "data/<id>",
        "rel_dest_path": "data/<newid2>",
        "filter_condition": {"vehicle_id": "V2", "route_id": 5}
    },
    "inputs": {
    },
    "outputs":
    {
    },
    "input_artifacts": {
        "data": ["<id>"]
    },
    "output_artifacts": {
        "data": ["<newid2>"]
    },
    "savedState": {},
    "status": ""
}

```

## Export Data to Target Location

The serialized data of inputs and actual outputs are exported as a json for seamless use by subsequent consumers.

```
overall_dict = {
    'inputs': overall_input,
    'outputs': {
        'prediction': [],
        'actual': overall_actual_output
    }
}
```

<br/>
<br/>

Back to [techniques.md](../../../../../../docs/techniques.md)
