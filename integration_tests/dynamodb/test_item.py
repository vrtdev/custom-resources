import boto3
import pytest
from troposphere import Template, constants, Parameter, Ref, dynamodb, Equals, If, Output

import custom_resources.dynamodb
from conftest import CloudFormationStates, delete_stack, create_stack, update_stack


@pytest.fixture(scope="module")
def template():
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

    template.add_resource(custom_resources.dynamodb.Item(
        "Item",
        TableName=If(table1_selected, Ref(table1), Ref(table2)),
        ItemKey={'key': {'S': Ref(key)}},
        ItemValue={'value': {'S': Ref(value)}},
        Overwrite=Ref(overwrite),
    ))

    return template


def test_item(cloudformation_stack_name, template):
    cfn_params = {
        "CustomResourcesStack": "vrt-dpc-custom-resources-2-stag",
        "Table": "1",
        "Key": "foo",
        "Value": "bar",
        "Overwrite": "false",
    }

    # create stack
    outputs, stack_id = create_stack(cfn_params, cloudformation_stack_name, template)

    table1_name = outputs['Table1Name']
    table2_name = outputs['Table2Name']
    key = {"key": {"S": "foo"}}

    ddb_client = boto3.client('dynamodb')

    def get_item(table_name):
        return ddb_client.get_item(
            TableName=table_name,
            Key=key,
        )

    item = get_item(table1_name)
    assert {
               "key": {"S": "foo"},
               "value": {"S": "bar"},
           } == item['Item']

    # update value
    cfn_params['Value'] = "42"

    update_stack(cfn_params, stack_id)

    item = get_item(table1_name)
    assert {
               "key": {"S": "foo"},
               "value": {"S": "42"},
           } == item['Item']

    # switch table
    cfn_params['Table'] = "2"

    update_stack(cfn_params, stack_id)

    item = get_item(table1_name)
    assert 'Item' not in item

    item = get_item(table2_name)
    assert {
               "key": {"S": "foo"},
               "value": {"S": "42"},
           } == item['Item']

    # already exists
    ddb_client.put_item(
        TableName=outputs['Table1Name'],
        Item={
            "key": {"S": "foo"},
            "value": {"S": "already here"}
        },
    )

    cfn_params['Table'] = "1"

    update_stack(cfn_params, stack_id, CloudFormationStates.UPDATE_ROLLBACK_COMPLETE)

    item = get_item(table1_name)
    assert {
               "key": {"S": "foo"},
               "value": {"S": "already here"},
           } == item['Item']

    item = get_item(table2_name)
    assert {
               "key": {"S": "foo"},
               "value": {"S": "42"},
           } == item['Item']

    # overwrite
    cfn_params['Table'] = "1"
    cfn_params['Overwrite'] = "true"

    update_stack(cfn_params, stack_id)

    item = get_item(table1_name)
    assert {
               "key": {"S": "foo"},
               "value": {"S": "42"},
           } == item['Item']

    item = get_item(table2_name)
    assert 'Item' not in item

    # cleanup
    delete_stack(stack_id)

