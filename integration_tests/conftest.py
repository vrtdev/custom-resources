import enum
import time
import typing
import warnings

import botocore.exceptions
import pytest
import boto3


class CloudFormationStates(enum.Enum):
    # https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-describing-stacks.html
    CREATE_COMPLETE = enum.auto()
    CREATE_IN_PROGRESS = enum.auto()
    CREATE_FAILED = enum.auto()
    DELETE_COMPLETE = enum.auto()
    DELETE_FAILED = enum.auto()
    DELETE_IN_PROGRESS = enum.auto()
    REVIEW_IN_PROGRESS = enum.auto()
    ROLLBACK_COMPLETE = enum.auto()
    ROLLBACK_FAILED = enum.auto()
    ROLLBACK_IN_PROGRESS = enum.auto()
    UPDATE_COMPLETE = enum.auto()
    UPDATE_COMPLETE_CLEANUP_IN_PROGRESS = enum.auto()
    UPDATE_IN_PROGRESS = enum.auto()
    UPDATE_ROLLBACK_COMPLETE = enum.auto()
    UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS = enum.auto()
    UPDATE_ROLLBACK_FAILED = enum.auto()
    UPDATE_ROLLBACK_IN_PROGRESS = enum.auto()


CloudFormationStatesStable = {
    CloudFormationStates.CREATE_COMPLETE,
    CloudFormationStates.CREATE_FAILED,
    CloudFormationStates.ROLLBACK_COMPLETE,
    CloudFormationStates.ROLLBACK_FAILED,
    CloudFormationStates.UPDATE_COMPLETE,
    CloudFormationStates.UPDATE_ROLLBACK_COMPLETE,
    CloudFormationStates.UPDATE_ROLLBACK_FAILED,
    CloudFormationStates.DELETE_COMPLETE,
    CloudFormationStates.DELETE_FAILED,
}


def wait_until_stack_in_state(
        stack_name_or_id: str,
        state: typing.Set[CloudFormationStates],
        poll_interval: int = 15,
        max_num_of_polls: int = 240,
) -> CloudFormationStates:
    """
    Waits until a given stack is in (one of) the given states.
    This function will (try to) resolve the name to the ID, so it can track stacks until
    the DELETE_COMPLETE
    :return: the actual state the resources is in after waiting
    """
    cfn_client = boto3.client('cloudformation', region_name='eu-west-1')
    active_stacks = cfn_client.describe_stacks(
        StackName=stack_name_or_id,
    )
    if len(active_stacks['Stacks']) == 0:
        # Stack not found, either it never existed, or it has been deleted
        if CloudFormationStates.DELETE_COMPLETE in state:
            # DELETE_COMPLETE was a desired state, so let's assume we reached that
            return CloudFormationStates.DELETE_COMPLETE
        raise ValueError(f"Stack `{stack_name_or_id}` not found")

    stack_name_or_id = active_stacks['Stacks'][0]['StackId']
    # Switch to using the ID, so we can track a stack into DELETE_COMPLETED

    while CloudFormationStates[active_stacks['Stacks'][0]['StackStatus']] not in state:
        if max_num_of_polls == 0:
            raise TimeoutError(f"Maxmimum number of polls reached. Stack {stack_name_or_id} did not reach desired state."
                               f" Current state: {active_stacks['Stacks'][0]['StackStatus']}")
        max_num_of_polls -= 1
        time.sleep(poll_interval)

        active_stacks = cfn_client.describe_stacks(
            StackName=stack_name_or_id,
        )

    return CloudFormationStates[active_stacks['Stacks'][0]['StackStatus']]


def wait_until_stack_stable(stack_name_or_id: str, **kwargs) -> CloudFormationStates:
    return wait_until_stack_in_state(
        stack_name_or_id=stack_name_or_id,
        state=CloudFormationStatesStable,
        **kwargs,
    )


test_number = 1


@pytest.fixture
def cloudformation_stack_name(request):
    del request  # unused
    global test_number
    stack_name = f"CustomResources-integration-test-{test_number}"
    test_number += 1

    yield stack_name

    # Make sure the stack is deleted
    cfn_client = boto3.client('cloudformation', region_name='eu-west-1')
    try:
        active_stacks = cfn_client.describe_stacks(
            StackName=stack_name,
        )
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Message'].endswith('does not exist'):
            return
        raise

    stack_status = CloudFormationStates[active_stacks['Stacks'][0]['StackStatus']]

    if stack_status in (
            CloudFormationStates.CREATE_IN_PROGRESS,
            CloudFormationStates.UPDATE_IN_PROGRESS,
    ):
        warnings.warn(f"Found stack in {stack_status} in teardown. Something is wrong in the test code")

    if stack_status in (
            CloudFormationStates.CREATE_IN_PROGRESS,
            CloudFormationStates.UPDATE_IN_PROGRESS,
            CloudFormationStates.UPDATE_COMPLETE_CLEANUP_IN_PROGRESS,
            CloudFormationStates.DELETE_IN_PROGRESS,
            CloudFormationStates.ROLLBACK_IN_PROGRESS,
            CloudFormationStates.UPDATE_ROLLBACK_IN_PROGRESS,
            CloudFormationStates.UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS,
    ):
        print(f"Stack {stack_name} is not ready: {stack_status}, waiting...")
        # Wait until the stack stabilizes
        stack_status = wait_until_stack_in_state(stack_name, CloudFormationStatesStable)
        print(f"Stack {stack_name} became stable: {stack_status}")

    if stack_status == CloudFormationStates.DELETE_COMPLETE:
        pass
    elif stack_status in (
            CloudFormationStates.CREATE_COMPLETE,
            CloudFormationStates.CREATE_FAILED,
            CloudFormationStates.ROLLBACK_COMPLETE,
            CloudFormationStates.ROLLBACK_FAILED,
            CloudFormationStates.UPDATE_COMPLETE,
            CloudFormationStates.UPDATE_ROLLBACK_COMPLETE,
            CloudFormationStates.UPDATE_ROLLBACK_FAILED,
    ):
        print(f"Deleting stack {stack_name}")
        cfn_client.delete_stack(
            StackName=stack_name,
        )
        wait_until_stack_in_state(stack_name, {
            CloudFormationStates.DELETE_COMPLETE,
        })
    else:
        raise RuntimeError(f"Stack {stack_name} is in state I can't fix: {stack_status}")


def create_stack(cfn_params, stack_name, template):
    cfn_client = boto3.client('cloudformation', region_name='eu-west-1')

    stack_id = cfn_client.create_stack(
        StackName=stack_name,
        TemplateBody=template.to_json(),
        Parameters=dict_to_param_array(cfn_params),
    )
    stack_id = stack_id['StackId']
    stack_state = wait_until_stack_stable(stack_id)

    assert CloudFormationStates.CREATE_COMPLETE == stack_state

    stack_info = cfn_client.describe_stacks(
        StackName=stack_id,
    )
    outputs = {
        _['OutputKey']: _['OutputValue']
        for _ in stack_info['Stacks'][0]['Outputs']
    }

    return outputs, stack_id


def update_stack(cfn_params, stack_id, expected_state=CloudFormationStates.UPDATE_COMPLETE):
    cfn_client = boto3.client('cloudformation', region_name='eu-west-1')
    cfn_client.update_stack(
        StackName=stack_id,
        UsePreviousTemplate=True,
        Parameters=dict_to_param_array(cfn_params),
    )
    assert expected_state == wait_until_stack_stable(stack_id)


def delete_stack(stack_id):
    cfn_client = boto3.client('cloudformation', region_name='eu-west-1')
    cfn_client.delete_stack(
        StackName=stack_id,
    )
    assert CloudFormationStates.DELETE_COMPLETE == wait_until_stack_stable(stack_id)


def dict_to_param_array(d):
    a = []
    for k, v in d.items():
        a.append({"ParameterKey": k, "ParameterValue": v})
    return a
