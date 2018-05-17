Custom resources
================

This repository holds custom resources that can be used by other cloudformation
templates.


Format
------

A custom resources consists of minimum:
 * a `CustomResourceName.py` file in the `custom_resources` directory
 * a python-file inside `lambda_handler/CustomResourceName` containing the
   lambda handler. By default, the function `handler(event, context)` in the
   file `index.py` is called, but that can be overridden by changing the
   `handler`-setting in the `_update_lambda_settings()`-hook
 
The `CustomResourceName.py` file defines the custom resource as it can be used
in Troposphere templates. It should define a single class with the same name,
deriving from the `LambdaBackedCustomResource` class.

The files in the `CustomResourceName` directory implement the actual code for 
the custom resource.


Building
--------

The build script gathers all custom resources in a single (generated)
CloudFormation template. When a directory contains a `requirements.txt` file,
it is used to bundle dependencies in the Lambda function.
