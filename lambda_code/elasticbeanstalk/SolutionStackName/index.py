"""
Custom Resource for finding latest the EB Solution Stack from a given filter set

Parameters:
    Platform: required: e.g. "PHP 7.0"
    Architecture: (default: 64bit)
    AmiStartsWith: (default: '')
    EbMajorVersion: (default: None)
    EbMinorVersion: (default: None)
    EbPatchVersion: (default: None)
    Serial: dummy, use this to force an update
"""
import re

from cfn_custom_resource import CloudFormationCustomResource
try:
    from _metadata import CUSTOM_RESOURCE_NAME
except ImportError:
    CUSTOM_RESOURCE_NAME = 'dummy'


platform_pattern = re.compile(
    r'^(?P<arch>\w+) (?P<ami>[\w .]+?)'
    r'(?: v(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+))?'
    r' running (?P<platform>.+)$',
)


class SolutionStackName(CloudFormationCustomResource):
    RESOURCE_TYPE_SPEC = CUSTOM_RESOURCE_NAME
    DISABLE_PHYSICAL_RESOURCE_ID_GENERATION = True  # Return StackName as physical ID

    def validate(self):
        self.filter = {}

        try:
            self.filter['platform'] = self.resource_properties['Platform']
            self.filter['arch'] = self.resource_properties.get('Architecture', '64bit')

            if self.resource_properties.get('EbMajorVersion') is not None:
                self.filter['major'] = int(self.resource_properties['EbMajorVersion'])
            if self.resource_properties.get('EbMinorVersion') is not None:
                self.filter['minor'] = int(self.resource_properties['EbMinorVersion'])
            if self.resource_properties.get('EbPatchVersion') is not None:
                self.filter['patch'] = int(self.resource_properties['EbPatchVersion'])

            self.ami_starts_with = self.resource_properties.get('AmiStartsWith', '')

            return True

        except (AttributeError, KeyError):
            return False

    @staticmethod
    def split_solution_stack_name(solution_stack_name):
        """Attempts to split the string in to its components"""

        match = re.search(platform_pattern, solution_stack_name)

        group_dict = match.groupdict()
        for x in ('major', 'minor', 'patch'):
            group_dict[x] = int(group_dict[x]) if group_dict.get(x) is not None else None

        return group_dict

    def filter_stack(self, stack_dict):
        for key, value in self.filter.items():
            if not stack_dict[key].startswith(value):
                return False
        # All filter items match

        return stack_dict['ami'].startswith(self.ami_starts_with)

    def create(self):
        eb_client = self.get_boto3_client('elasticbeanstalk')

        all_stacks = eb_client.list_available_solution_stacks()['SolutionStacks']

        filtered_stacks = [
            s
            for s in all_stacks
            if self.filter_stack(self.split_solution_stack_name(s))
        ]

        self.physical_resource_id = filtered_stacks[0]  # May raise IndexError
        return {}

    def update(self):
        return self.create()

    def delete(self):
        # Nothing to delete
        pass


handler = SolutionStackName.get_handler()
