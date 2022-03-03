grpcurl \
--plaintext \
-d '{"service":"modelservice"}' \
-import-path ${PWD} \
-proto health.proto \
-proto model_interface.proto \
localhost:13000 grpc.health.v1.Health/Check