"""CloudFormation template to create custom resource Lambda's"""
import os
import importlib
import argparse
import shutil
import typing
import zipfile

import pip
import troposphere
from troposphere import Template, awslambda, logs, Sub, Output, Export, GetAtt, constants
from central_helpers import MetadataHelper, vrt

parser = argparse.ArgumentParser(description='Build custom resources CloudForamtion template')
parser.add_argument('--class-dir', help='Where to look for the CustomResource classes',
                    default='custom_resources')
parser.add_argument('--lambda-dir', help='Where to look for defined Lambda functions',
                    default='lambda_code')
parser.add_argument('--output-dir', help='Where to place the Zip-files and the CloudFormation template',
                    default='output')

args = parser.parse_args()


template = Template("Custom Resources")
template_helper = MetadataHelper(template)
vrt_tags = vrt.add_tags(template)

s3_bucket = template.add_parameter(troposphere.Parameter(
    "S3Bucket",
    Type=constants.STRING,
    Description="S3 bucket where the ZIP files are located",
))
template_helper.add_parameter_label(s3_bucket, "S3 bucket")

s3_path = template.add_parameter(troposphere.Parameter(
    "S3Path",
    Type=constants.STRING,
    Default='',
    Description="Path prefix where the ZIP files are located (should probably end with a '/')",
))
template_helper.add_parameter_label(s3_path, "S3 path")

template_helper.add_parameter_group("Lambda code location", [s3_bucket, s3_path])


def defined_custom_resources(lambda_dir: str, class_dir: str) -> typing.Set[str]:
    """
    Find custom resources matching our requirements
    """
    custom_resources = {
        'py': set(),
        'dir': set(),
    }
    for entry in os.scandir(lambda_dir):
        if entry.name.startswith('.'):
            continue
        if entry.is_dir():
            custom_resources['dir'].add(entry.name)

    for entry in os.scandir(class_dir):
        if entry.name.startswith('.'):
            continue
        if entry.is_file():
            custom_resources['py'].add(entry.name[:-3])

    return custom_resources['py'] & custom_resources['dir']


def create_zip_file(lambda_dir: str, resource_name: str, output_dir: str):
    print(f"Creating ZIP for resource {resource_name}")
    with zipfile.ZipFile(os.path.join(output_dir, f"{resource_name}.zip"),
                         mode='w',
                         compression=zipfile.ZIP_DEFLATED) as zip:

        entries = set(os.scandir(os.path.join(lambda_dir, resource_name)))

        # See if there is a top-level `requirements.txt`
        requirements = None
        for entry in entries:
            if entry.name == 'requirements.txt':
                requirements = entry
                break  # filenames are unique, no need to continue once found

        if requirements is not None:
            # `requirements.txt` found. Interpret it, and add the result to the zip file
            entries.remove(requirements)
            pip_dir = os.path.join(output_dir, resource_name)
            pip.main(['install', '-r', requirements.path, '-t', pip_dir])
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
                lambda_prefix = f"{lambda_dir}/{resource_name}/"
                if zip_path.startswith(lambda_prefix):
                    zip_path = zip_path[(len(lambda_prefix)):]
                if requirements is not None and zip_path.startswith(pip_dir):
                    zip_path = zip_path[(len(pip_dir)+1):]

                zip.write(entry.path, zip_path)

        if requirements is not None:
            shutil.rmtree(pip_dir)

    print("ZIP done for resource {resource_name}".format(resource_name=resource_name))
    print("")


try:
    os.mkdir(args.output_dir)
except FileExistsError:
    pass

for custom_resource_name in defined_custom_resources(args.lambda_dir, args.class_dir):
    create_zip_file(args.lambda_dir, custom_resource_name, args.output_dir)

    custom_resource_mod = importlib.import_module(f'.{custom_resource_name}', args.class_dir)
    custom_resource_class = getattr(custom_resource_mod, custom_resource_name)

    role = template.add_resource(custom_resource_class.lambda_role(
        f"{custom_resource_name}Role",
    ))
    awslambdafunction = template.add_resource(awslambda.Function(
        f"{custom_resource_name}Function",
        Code=awslambda.Code(
            S3Bucket=troposphere.Ref(s3_bucket),
            S3Key=troposphere.Join('', [troposphere.Ref(s3_path), f"{custom_resource_name}.zip"]),
        ),
        Role=GetAtt(role, 'Arn'),
        Tags=troposphere.Tags(**vrt_tags),
        **custom_resource_class.function_settings()
    ))
    template.add_resource(logs.LogGroup(
        f"{custom_resource_name}Logs",
        LogGroupName=Sub(f"/aws/lambda/{custom_resource_name}"),
        RetentionInDays=90,
    ))
    template.add_output(Output(
        f"{custom_resource_name}ServiceToken",
        Value=GetAtt(awslambdafunction, 'Arn'),
        Description=f"ServiceToken for the {custom_resource_name} custom resource",
        Export=Export(Sub(f"${{AWS::StackName}}-{custom_resource_name}ServiceToken"))
    ))
    template.add_output(Output(
        f"{custom_resource_name}Role",
        Value=GetAtt(role, 'Arn'),
        Description=f"Role used by the {custom_resource_name} custom resource",
        Export=Export(Sub(f"${{AWS::StackName}}-{custom_resource_name}Role")),
    ))

with open(os.path.join(args.output_dir, 'cfn.json'), 'w') as f:
    f.write(template.to_json())
