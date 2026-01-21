import pytest
from troposphere import Template, Sub, GetAtt, Output

import custom_resources.cloudformation
import custom_resources.ssm
from conftest import delete_stack, create_stack


@pytest.fixture(scope="module")
def template():
    template = Template()

    custom_resources.use_custom_resources_stack_name_parameter(template)
    cloudformation_tags = template.add_resource(custom_resources.cloudformation.Tags("CfnTags"))

    dummy_test_secret_parameter = template.add_resource(custom_resources.ssm.Parameter(
        "DummyTestSecretParameter",
        Name=Sub('/${AWS::StackName}/my-secret-test-token-shhhht'),
        Type="SecureString",
        RandomValue={'serial': 1},  # increment to rotate pwd
        Tags=GetAtt(cloudformation_tags, "TagList"),
    ))

    template.add_output(Output(
        "DummyTestSecretParameterArn",
        Value=GetAtt(dummy_test_secret_parameter, "Arn"),
    ))

    return template


def test_item(cloudformation_stack_name, template):
    cfn_params = {
        "CustomResourcesStack": "vrt-dpc-custom-resources-2-stag",
    }

    # create stack
    outputs, stack_id = create_stack(cfn_params, cloudformation_stack_name, template)

    # TODO assert something

    # cleanup
    delete_stack(stack_id)

