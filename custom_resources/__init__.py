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
        parameter_kwargs_dict=None,
):
    if parameter_kwargs_dict is None:
        parameter_kwargs_dict = {}

    param_kwargs = {  # defaults
        'Type': troposphere.constants.STRING,
        'Default': "custom-resources",
        'Description': "Name of the custom resources stack",
    }
    param_kwargs.update(parameter_kwargs_dict)

    p = template.add_parameter(troposphere.Parameter(
        parameter_title,
        **param_kwargs
    ))

    global CUSTOM_RESOURCES_STACK_NAME
    CUSTOM_RESOURCES_STACK_NAME = troposphere.Ref(p)

    return p
