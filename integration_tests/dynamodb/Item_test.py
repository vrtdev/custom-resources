import boto3
from troposphere import Template, constants, Parameter, Ref, dynamodb, Equals, If, Output

import custom_resources.dynamodb

from integration_tests.conftest import CloudFormationStates, wait_until_stack_stable, dict_to_param_array

template = Template()

table = template.add_parameter(Parameter(
    "Table",
    Type=constants.STRING,
    AllowedValues=["1", "2"],
    Default='1',
    Description="Key"
))
key = template.add_parameter(Parameter(
    "Key",
    Type=constants.STRING,
    Default='foo',
    Description="Key"
))
value = template.add_parameter(Parameter(
    "Value",
    Type=constants.STRING,
    Default='bar',
    Description="value"
))
overwrite = template.add_parameter(Parameter(
    "Overwrite",
    Type=constants.STRING,
    AllowedValues=['true', 'false'],
    Default='false',
    Description="overwrite",
))

custom_resources.use_custom_resources_stack_name_parameter(template)

table1 = template.add_resource(dynamodb.Table(
    "Table1",
    BillingMode="PAY_PER_REQUEST",
    AttributeDefinitions=[
        dynamodb.AttributeDefinition(
            AttributeName="key",
            AttributeType="S",
        )
    ],
    KeySchema=[
        dynamodb.KeySchema(
            AttributeName="key",
            KeyType="HASH",
        )
    ],
))

template.add_output(Output(
    "Table1Name",
    Value=Ref(table1),
))

table2 = template.add_resource(dynamodb.Table(
    "Table2",
    BillingMode="PAY_PER_REQUEST",
    AttributeDefinitions=[
        dynamodb.AttributeDefinition(
            AttributeName="key",
            AttributeType="S",
        )
    ],
    KeySchema=[
        dynamodb.KeySchema(
            AttributeName="key",
            KeyType="HASH",
        )
    ],
))

template.add_output(Output(
    "Table2Name",
    Value=Ref(table2),
))


table1_selected = template.add_condition("Table1Selected", Equals(Ref(table), '1'))

table_item = template.add_resource(custom_resources.dynamodb.Item(
    "Item",
    TableName=If(table1_selected, Ref(table1), Ref(table2)),
    ItemKey={'key': {'S': Ref(key)}},
    ItemValue={'value': {'S': Ref(value)}},
    Overwrite=Ref(overwrite),
))


def test_item(cloudformation_stack_name):
    cfn_params = {
        "CustomResourcesStack": "vrt-dpc-custom-resources-2-stag",
        "Table": "1",
        "Key": "foo",
        "Value": "bar",
        "Overwrite": "false",
    }

    outputs, stack_id = create_stack(cfn_params, cloudformation_stack_name)

    update_value(cfn_params, outputs, stack_id)

    switch_table(cfn_params, outputs, stack_id)

    already_exists(cfn_params, outputs, stack_id)

    already_exists_overwrite(cfn_params, outputs, stack_id)

    delete_stack(cfn_params, outputs, stack_id)


def create_stack(cfn_params, stack_name):
    cfn_client = boto3.client('cloudformation')

    stack_id = cfn_client.create_stack(
        StackName=stack_name,
        TemplateBody=template.to_json(),
        Parameters=dict_to_param_array(cfn_params),
    )
    stack_id = stack_id['StackId']
    assert CloudFormationStates.CREATE_COMPLETE == wait_until_stack_stable(stack_id)
    stack_info = cfn_client.describe_stacks(
        StackName=stack_id,
    )
    outputs = {
        _['OutputKey']: _['OutputValue']
        for _ in stack_info['Stacks'][0]['Outputs']
    }
    ddb_client = boto3.client('dynamodb')
    item = ddb_client.get_item(
        TableName=outputs['Table1Name'],
        Key={"key": {"S": "foo"}},
    )
    assert {
               "key": {"S": "foo"},
               "value": {"S": "bar"},
           } == item['Item']

    return outputs, stack_id


def update_value(cfn_params, outputs, stack_id):
    cfn_client = boto3.client('cloudformation')
    cfn_params['Value'] = "42"
    cfn_client.update_stack(
        StackName=stack_id,
        UsePreviousTemplate=True,
        Parameters=dict_to_param_array(cfn_params),
    )
    assert CloudFormationStates.UPDATE_COMPLETE == wait_until_stack_stable(stack_id)
    ddb_client = boto3.client('dynamodb')
    item = ddb_client.get_item(
        TableName=outputs['Table1Name'],
        Key={"key": {"S": "foo"}},
    )
    assert {
               "key": {"S": "foo"},
               "value": {"S": "42"},
           } == item['Item']


def switch_table(cfn_params, outputs, stack_id):
    cfn_client = boto3.client('cloudformation')
    cfn_params['Table'] = "2"
    cfn_client.update_stack(
        StackName=stack_id,
        UsePreviousTemplate=True,
        Parameters=dict_to_param_array(cfn_params),
    )
    assert CloudFormationStates.UPDATE_COMPLETE == wait_until_stack_stable(stack_id)

    ddb_client = boto3.client('dynamodb')
    item = ddb_client.get_item(
        TableName=outputs['Table1Name'],
        Key={"key": {"S": "foo"}},
    )
    assert 'Item' not in item

    item = ddb_client.get_item(
        TableName=outputs['Table2Name'],
        Key={"key": {"S": "foo"}},
    )
    assert {
               "key": {"S": "foo"},
               "value": {"S": "42"},
           } == item['Item']


def already_exists(cfn_params, outputs, stack_id):
    ddb_client = boto3.client('dynamodb')
    ddb_client.put_item(
        TableName=outputs['Table1Name'],
        Item={
            "key": {"S": "foo"},
            "value": {"S": "already here"}
        },
    )

    cfn_client = boto3.client('cloudformation')
    cfn_params['Table'] = "1"
    cfn_client.update_stack(
        StackName=stack_id,
        UsePreviousTemplate=True,
        Parameters=dict_to_param_array(cfn_params),
    )
    assert CloudFormationStates.UPDATE_ROLLBACK_COMPLETE == wait_until_stack_stable(stack_id)

    ddb_client = boto3.client('dynamodb')
    item = ddb_client.get_item(
        TableName=outputs['Table1Name'],
        Key={"key": {"S": "foo"}},
    )
    assert {
           "key": {"S": "foo"},
           "value": {"S": "already here"},
       } == item['Item']

    item = ddb_client.get_item(
        TableName=outputs['Table2Name'],
        Key={"key": {"S": "foo"}},
    )
    assert {
               "key": {"S": "foo"},
               "value": {"S": "42"},
           } == item['Item']


def already_exists_overwrite(cfn_params, outputs, stack_id):
    cfn_client = boto3.client('cloudformation')
    cfn_params['Table'] = "1"
    cfn_params['Overwrite'] = "true"
    cfn_client.update_stack(
        StackName=stack_id,
        UsePreviousTemplate=True,
        Parameters=dict_to_param_array(cfn_params),
    )
    assert CloudFormationStates.UPDATE_COMPLETE == wait_until_stack_stable(stack_id)

    ddb_client = boto3.client('dynamodb')
    item = ddb_client.get_item(
        TableName=outputs['Table1Name'],
        Key={"key": {"S": "foo"}},
    )
    assert {
               "key": {"S": "foo"},
               "value": {"S": "42"},
           } == item['Item']

    item = ddb_client.get_item(
        TableName=outputs['Table2Name'],
        Key={"key": {"S": "foo"}},
    )
    assert 'Item' not in item


def delete_stack(cfn_params, outputs, stack_id):
    cfn_client = boto3.client('cloudformation')
    cfn_client.delete_stack(
        StackName=stack_id,
    )
    assert CloudFormationStates.DELETE_COMPLETE == wait_until_stack_stable(stack_id)
