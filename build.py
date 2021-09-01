"""
Build script for custom resources.

This script scans the `class-dir` and `lambda-dir` directories to generate a
list of defined custom resources. For each discovered resource, it creates a
ZIP-file, and adds the resource to the generated CloudFormation template to
be deployed.
"""
import os
import importlib
import subprocess
import sys

import argparse
import shutil
import typing
import zipfile

try:
    from pip import main as pipmain  # pip 9
except ImportError:
    from pip._internal import main as pipmain  # pip 10

import troposphere
from troposphere import Template, awslambda, logs, Sub, Output, Export, GetAtt, constants, Ref, Not, Equals, Join, ec2
from custom_resources.LambdaBackedCustomResource import LambdaBackedCustomResource

parser = argparse.ArgumentParser(description='Build custom resources CloudFormation template')
parser.add_argument('--class-dir', help='Where to look for the CustomResource classes',
                    default='custom_resources')
parser.add_argument('--lambda-dir', help='Where to look for defined Lambda functions',
                    default='lambda_code')
parser.add_argument('--output-dir', help='Where to place the Zip-files and the CloudFormation template',
                    default='output')

args = parser.parse_args()


template = Template("Custom Resources")

s3_bucket = template.add_parameter(troposphere.Parameter(
    "S3Bucket",
    Type=constants.STRING,
    Description="S3 bucket where the ZIP files are located",
))
template.set_parameter_label(s3_bucket, "S3 bucket")
lambda_code_location = template.add_parameter_to_group(s3_bucket, "Lambda code location")

s3_path = template.add_parameter(troposphere.Parameter(
    "S3Path",
    Type=constants.STRING,
    Default='',
    Description="Path prefix where the ZIP files are located (should probably end with a '/')",
))
template.set_parameter_label(s3_path, "S3 path")
template.add_parameter_to_group(s3_path, lambda_code_location)

vpc_subnets = template.add_parameter(troposphere.Parameter(
    "VpcSubnets",
    # Type cannot be a list of subnets ids if we want them to also support being empty
    Type=constants.COMMA_DELIMITED_LIST,
    Default="",
    Description="(optional) VPC subnets for Custom Resources that run attached to a VPC"
))
template.set_parameter_label(vpc_subnets, "VPC Subnets")
vpc_settings = template.add_parameter_to_group(vpc_subnets, "VPC Settings")

has_vpc_subnets = template.add_condition("HasVpcSubnets", Not(Equals(Join("", Ref(vpc_subnets)), "")))


def rec_split_path(path: str) -> typing.List[str]:
    """
    Split a path in its components.

    Much like os.path.split(), but "recursively".
    """
    l = []
    head = path
    while len(head) > 0:
        head, tail = os.path.split(head)
        l.insert(0, tail)
    return l


def rec_join_path(path_list: typing.List[str]) -> str:
    """
    Join components in to a path.

    Much like os.path.join(), but "recursively".
    """
    if len(path_list) == 0:
        return ''
    if len(path_list) == 1:
        return path_list[0]
    path = path_list.pop(0)
    while len(path_list):
        path = os.path.join(path, path_list.pop(0))
    return path


class CustomResource:
    def __init__(
            self,
            name: typing.List[str],
            lambda_path: str,
            troposphere_class: LambdaBackedCustomResource
    ):
        self.name = name
        self.lambda_path = lambda_path
        self.troposphere_class = troposphere_class

    def __eq__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.troposphere_class == other.troposphere_class

    def __hash__(self):
        return hash(self.troposphere_class)


def defined_custom_resources(lambda_dir: str, class_dir: str) -> typing.Set[CustomResource]:
    """
    Find custom resources matching our requirements.
    """
    custom_resources = set()
    for dirpath, dirs, files in os.walk(class_dir):
        for file in files:
            if file.startswith('.'):
                continue
            if file.startswith('_'):
                continue
            if not file.endswith('.py'):
                continue

            # load the found Python module
            file_without_py = file[:-3]
            relative_dir = dirpath[len(class_dir) + 1:]
            fs_path = os.path.join(relative_dir, file_without_py)

            module_location = rec_split_path(fs_path)
            mod = importlib.import_module(
                '.' + '.'.join(module_location),
                os.path.basename(class_dir)
            )

            for candidate_class_name in dir(mod):
                if candidate_class_name.startswith('_'):
                    continue
                candidate_class = getattr(mod, candidate_class_name)
                if not isinstance(candidate_class, type):
                    continue
                # candidate_class is a class; check for a matching directory in lambda_dir

                lambda_code_dir = rec_join_path([lambda_dir, fs_path, candidate_class_name])
                if os.path.isdir(lambda_code_dir):
                    custom_resources.add(CustomResource(
                        name=[*module_location, candidate_class_name],
                        lambda_path=lambda_code_dir,
                        troposphere_class=candidate_class,
                    ))

    return custom_resources


def run_pip(*args):
    subprocess.run(
        ['pip', *args],
        check=True,
    )


def create_zip_file(custom_resource: CustomResource, output_dir: str):
    dot_joined_resource_name = '.'.join(custom_resource.name)

    print("Creating ZIP for resource {}".format(dot_joined_resource_name))

    zip_filename = "{}.zip".format(dot_joined_resource_name)
    zip_full_filename = os.path.join(output_dir, zip_filename)
    with zipfile.ZipFile(zip_full_filename,
                         mode='w',
                         compression=zipfile.ZIP_DEFLATED) as zip:

        entries = set(os.scandir(custom_resource.lambda_path))

        # See if there is a top-level `requirements.txt` or `test`
        requirements_file = None
        test_file = None
        for entry in entries:
            if entry.name == 'requirements.txt':
                requirements_file = entry
            elif entry.name == 'test':
                test_file = entry

        pip_dir = os.path.join(output_dir, dot_joined_resource_name)
        os.mkdir(pip_dir)

        if requirements_file is not None:
            # `requirements.txt` found. Interpret it, and add the result to the zip file
            entries.remove(requirements_file)
            run_pip('install',
                    '-r', requirements_file.path,
                    '--isolated',  # Don't automatically add --user (which breaks --target below)
                                   # --user is on by default on (at least) Debian Buster
                    '--target', pip_dir)

        if test_file is not None:
            entries.remove(test_file)

        # Generate _metadata.py file
        with open(os.path.join(pip_dir, "_metadata.py"), "w") as f:
            f.write("CUSTOM_RESOURCE_NAME = \"{}\"\n".format(
                custom_resource.troposphere_class.custom_resource_name(
                    custom_resource.troposphere_class.name()
                )
            ))

        # Add installed/generated files to list to include in ZIP
        entries.update(set(os.scandir(pip_dir)))

        # add everything (recursively) to the zip file
        while len(entries):
            entry = entries.pop()

            if entry.is_dir():
                if entry.name == "__pycache__":
                    pass  # don't include cache
                else:
                    entries.update(set(os.scandir(entry.path)))

            elif entry.is_file():
                zip_path = entry.path
                lambda_prefix = custom_resource.lambda_path
                if zip_path.startswith(lambda_prefix):
                    zip_path = zip_path[(len(lambda_prefix)+1):]
                if zip_path.startswith(pip_dir):
                    zip_path = zip_path[(len(pip_dir)+1):]

                zip.write(entry.path, zip_path)

        shutil.rmtree(pip_dir)

    print("ZIP done for resource {}".format(dot_joined_resource_name))
    print("")
    return zip_filename


try:
    os.mkdir(args.output_dir)
except FileExistsError:
    pass

# Import the custom_resources package
sys.path.insert(0, os.path.dirname(args.class_dir))
importlib.import_module(os.path.basename(args.class_dir))

for custom_resource in defined_custom_resources(args.lambda_dir, args.class_dir):
    custom_resource_name_cfn = custom_resource.troposphere_class.cloudformation_name(
        custom_resource.troposphere_class.name()
    )

    zip_filename = create_zip_file(custom_resource, args.output_dir)

    function_settings = custom_resource.troposphere_class.function_settings()
    needs_vpc = False
    created_aws_objects: list[troposphere.BaseAWSObject] = []
    if "VpcConfig" in function_settings:
        needs_vpc = True
        security_group = template.add_resource(ec2.SecurityGroup(
            "{custom_resource_name}SecurityGroup".format(custom_resource_name=custom_resource_name_cfn),
            GroupDescription="Security Group for the {custom_resource_name} custom resource".format(
                custom_resource_name='.'.join(custom_resource.name)
            ),
        ))
        created_aws_objects.append(security_group)
        created_aws_objects.append(template.add_output(Output(
            "{custom_resource_name}SecurityGroup".format(custom_resource_name=custom_resource_name_cfn),
            Value=Ref(security_group),
            Description="Security Group used by the {custom_resource_name} custom resource".format(
                custom_resource_name='.'.join(custom_resource.name)
            ),
            Export=Export(Sub("${{AWS::StackName}}-{custom_resource_name}SecurityGroup".format(
                custom_resource_name=custom_resource_name_cfn,
            ))),
        )))

        function_settings["VpcConfig"] = awslambda.VPCConfig(
            SecurityGroupIds=[Ref(security_group)],
            SubnetIds=Ref(vpc_subnets)
        )

    role = template.add_resource(custom_resource.troposphere_class.lambda_role(
        "{custom_resource_name}Role".format(custom_resource_name=custom_resource_name_cfn),
    ))
    created_aws_objects.append(role)
    awslambdafunction = template.add_resource(awslambda.Function(
        "{custom_resource_name}Function".format(custom_resource_name=custom_resource_name_cfn),
        Code=awslambda.Code(
            S3Bucket=troposphere.Ref(s3_bucket),
            S3Key=troposphere.Join('', [troposphere.Ref(s3_path),
                                        zip_filename]),
        ),
        Role=GetAtt(role, 'Arn'),
        **function_settings
    ))
    created_aws_objects.append(awslambdafunction)
    created_aws_objects.append(template.add_resource(logs.LogGroup(
        "{custom_resource_name}Logs".format(custom_resource_name=custom_resource_name_cfn),
        LogGroupName=troposphere.Join('', ["/aws/lambda/", troposphere.Ref(awslambdafunction)]),
        RetentionInDays=90,
    )))
    created_aws_objects.append(template.add_output(Output(
        "{custom_resource_name}ServiceToken".format(custom_resource_name=custom_resource_name_cfn),
        Value=GetAtt(awslambdafunction, 'Arn'),
        Description="ServiceToken for the {custom_resource_name} custom resource".format(
            custom_resource_name='.'.join(custom_resource.name)
        ),
        Export=Export(Sub("${{AWS::StackName}}-{custom_resource_name}ServiceToken".format(
            custom_resource_name=custom_resource_name_cfn
        )))
    )))
    created_aws_objects.append(template.add_output(Output(
        "{custom_resource_name}Role".format(custom_resource_name=custom_resource_name_cfn),
        Value=GetAtt(role, 'Arn'),
        Description="Role used by the {custom_resource_name} custom resource".format(
            custom_resource_name='.'.join(custom_resource.name)
        ),
        Export=Export(Sub("${{AWS::StackName}}-{custom_resource_name}Role".format(
            custom_resource_name=custom_resource_name_cfn,
        ))),
    )))
    if needs_vpc:
        for aws_object in created_aws_objects:
            if aws_object.resource.get('Condition'):
                raise ValueError("Can't handle multiple conditions")
            aws_object.Condition = has_vpc_subnets

with open(os.path.join(args.output_dir, 'cfn.json'), 'w') as f:
    f.write(template.to_json())
