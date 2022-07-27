table_key_schema = [
    {'AttributeName': 'run_specifier', 'KeyType': 'HASH'},
    {'AttributeName': 'run_index', 'KeyType': 'RANGE'}
]

table_attribute_def = [
    {'AttributeName': 'run_specifier', 'AttributeType': 'S'},
    {'AttributeName': 'run_index', 'AttributeType': 'N'}
]
