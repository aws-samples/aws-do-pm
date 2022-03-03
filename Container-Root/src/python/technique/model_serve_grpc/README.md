# Model Serve using GRPC

The neural network model can be wrapped into a gRPC server that can expose the model for low-latency responses.

## Proto Object

The model service implements two methods
<li> EvaluateModel consumes an incoming request to generate the response</li>
<li> HealthCheck to determine the service status from an external client</li>

```
service ModelService {
    rpc EvaluateModel(inRequest) returns (outCalc) {};
    rpc HealthCheck(google.protobuf.Empty) returns (HCReply);
}
```

## Generic Model Server

The model_server.py has a very generic structure which comprises of 3 main parts. Any model that needs to be packed into the server has to implement the 3 constructs:
<li> Model Initialize: Initialize the underlying model into server memory and generate the objects that can be packed and passed on with incoming queries for an evaluation </li>
<li> Model Run: Takes the objects from Initialize and incoming request to trigger an evaluation</li>
<li> Model Cleanup </li>

In this specific use case the torchhandler_atomic.py has implemented the above 3 constructs.

## Accessing the server from client

The stub to access the server is created in the client. The interceptors are used to repeat the attempts in case of a delay with server startup.

```
address='%s:%s'%(hostname,port)

interceptors = (
    RetryOnRpcErrorClientInterceptor(
        max_attempts=5,
        sleeping_policy=ExponentialBackoff(init_backoff_ms=1000, max_backoff_ms=30000, multiplier=2),
        status_for_retry=(grpc.StatusCode.UNAVAILABLE,),
    ),
)
stub = model_interface_pb2_grpc.ModelServiceStub(
    grpc.intercept_channel(grpc.insecure_channel(address), *interceptors)
)
```

The stub can be used invoke the model evaluation with the payload. 
- Compose query from the input dictionary with all the information needed for the model
- Relay the query to the EvaluateModel function
- Collect the return message and decode the contents

```
query = model_interface_pb2.inRequest(inp_dict_bytes=loc_inp_dict_encoded)
nRuns = 1000
for _ in tqdm(range(nRuns)):
    response = stub.EvaluateModel(query)
```

<br/>
<br/>

Back to [techniques.md](../../../../docs/techniques.md)
