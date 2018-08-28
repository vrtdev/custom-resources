"""
Usage:

    template = troposphere.Template()

    # Optionally add a parameter to make the stackname of the Custom Resources configurable
    custom_resources.use_custom_resources_stack_name_parameter(template)

    template.add_resource(custom_resources.Possibly.Nested.SomeCR(
        "foo",
        Bar="baz"
    ))

"""
import troposphere
import troposphere.constants


CUSTOM_RESOURCES_STACK_NAME = 'custom-resources'


def _get_custom_resources_stack_name():
    if isinstance(CUSTOM_RESOURCES_STACK_NAME, troposphere.Ref):
        # Special case for Ref()
        # The string is rendered inside a Sub(), so we can replace the Ref() by a straight interpollation
        return "${{{}}}".format(
            CUSTOM_RESOURCES_STACK_NAME.data['Ref']
        )

    return CUSTOM_RESOURCES_STACK_NAME


def use_custom_resources_stack_name_parameter(
        template,
        parameter_title="CustomResourcesStack",
        default_value="custom-resources",
        description="Name of the custom resources stack",
):
    p = template.add_parameter(troposphere.Parameter(
        parameter_title,
        Type=troposphere.constants.STRING,
        Default=default_value,
        Description=description,
    ))

    global CUSTOM_RESOURCES_STACK_NAME
    CUSTOM_RESOURCES_STACK_NAME = troposphere.Ref(p)

    return p
