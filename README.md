Custom resources
================

This repository holds custom resources that can be used by other cloudformation
templates.


Format
------

A custom resources consists of minimum:
 * A python class somewhere in the `custom_resources` directory.
 * A directory with the same name/path in the `lambda_code` directory,
   containing the lambda handler.
   By default, the function `handler(event, context)` in the
   file `index.py` is called, but that can be overridden by changing the
   `handler`-setting in the `_update_lambda_settings()`-hook.

And preferably:
 * A (set of) integration tests in the `test` directory.

The python class defines the custom resource as it can be used in Troposphere
templates. It should derive from the `LambdaBackedCustomResource` class. You
can use an arbitrary hierarchy under the `custom_resources` package.

The files under the `lambda_code` directory implement the actual code for 
the custom resource. The code corresponding to a class `Resource` in the module
`custom_resources/Service/Subservice.py` should be a directory
`lambda_code/Service/Subservice/Resource/`. The generated ResourceType name is
`Custom::Service@Subservice@Resource`.


Building
--------

The build script (`build.py`) gathers all custom resources in a single (generated)
CloudFormation template. Each resource inside `lambda_code` is zipped.
The following (relative) paths are treated specially:

 * '/requirements.txt`: This file is interpreted to add dependencies in the
   ZIP file. The file itself is not included in the ZIP

 * '/test/**': The directory `test` is ignored, including its contents. This
   is the ideal location for unit tests.

 * '/_metadata.py': This file is generated at build-time. It contains various
   variable definitions that may come in handy at run-time, such as:

   - CUSTOM_RESOURCE_NAME: the custom resource name as will be used by depending
     templates. E.g. "Service@Foobar" for "Custom::Service@Foobar" resources.

### Step-by-Step instructions
You can also 
Assumptions:
- You're working in a virtualenv
- You have an S3 bucket to save the zip files in. We use `$S3_BUCKET` and `$S3_PATH` (should end in `/`)in the script below
- You are using the right profile or environemnt variables to have credentials for the `aws` command

```shell
# install requirements and build
pip install -r requirements.txt --upgrade
python build.py

# Upload the outputs
S3_BUCKET='a-bucket'
S3_PATH="custom-resources-$(date '+%s')"
aws s3 sync output/ s3://$S3_BUCKET/$S3_PATH
echo "uploaded to s3://$S3_BUCKET/$S3_PATH"

# Deploy the cloudformation template in output/cfn.json
```
