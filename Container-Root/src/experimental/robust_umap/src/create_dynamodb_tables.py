import boto3

def check_create_dynamodb_table(name, key_schema, attribute_def, region_name, dynamodb=None):
    if dynamodb is None:
        dynamodb = boto3.resource('dynamodb', region_name=region_name)
    dynamodb_client = dynamodb.meta.client

    # Check if table exists
    existing_tables = dynamodb_client.list_tables()['TableNames']
    if (name not in existing_tables):
        billing_mode = 'PAY_PER_REQUEST'
        table = dynamodb.create_table(
            TableName=name,
            KeySchema=key_schema,
            AttributeDefinitions=attribute_def,
            BillingMode=billing_mode
        )

        # Wait for table creation
        print('Waiting for', name, '...')
        waiter = dynamodb_client.get_waiter('table_exists')
        waiter.wait(TableName=name, WaiterConfig={'Delay': 1})
    else:
        print('Table Exists, Skipping Creation')
        table = dynamodb.Table(name)

    return table

if __name__ == "__main__":
    # from table_definition import table_name, ga_overview_table_name, ga_detail_table_name
    from table_definition import table_key_schema, table_attribute_def

    import configparser

    config = configparser.RawConfigParser()
    config.read('./template/config_template.conf')
    common_dict = config._sections['common']
    ga_dict = config._sections['GA']

    region_name = common_dict['region_name']
    table_name = ga_dict['table_name']
    ga_overview_table_name = ga_dict['ga_overview_table_name']
    ga_detail_table_name = ga_dict['ga_detail_table_name']

    session = boto3.session.Session()
    dynamodb = session.resource('dynamodb', region_name=region_name)

    # Create the workload table
    check_create_dynamodb_table(
        name=table_name,
        key_schema=table_key_schema,
        attribute_def=table_attribute_def,
        region_name=region_name,
        dynamodb=dynamodb
    )

    # Create the workload ga table
    check_create_dynamodb_table(
        name=ga_overview_table_name,
        key_schema=table_key_schema,
        attribute_def=table_attribute_def,
        region_name=region_name,
        dynamodb=dynamodb
    )

    check_create_dynamodb_table(
        name=ga_detail_table_name,
        key_schema=table_key_schema,
        attribute_def=table_attribute_def,
        region_name=region_name,
        dynamodb=dynamodb
    )
